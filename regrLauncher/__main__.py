import argparse
import pathlib
import json
import os
import pwd
import datetime
import re
import multiprocessing
#import concurrent.futures

from .queue import rlJobQueuer
from .runner import sessionBuildExecutor, sessionRunExecutor
from .report import JUnitXMLReport
from .utils import cstr, RED, GREEN, MAGENTA
from .utils import convert_value

from .database import init_db, sqlDbSession, SESSION_STATUS_ENUM

def propagate_attributes(dictionary):
    attributes = dict(filter(lambda item: not isinstance(item[1], dict), dictionary.items()))
    subhier = dict(filter(lambda item: isinstance(item[1], dict), dictionary.items()))
    for key, value in subhier.items():
        value = merge_parent_attributes(value, attributes)
        dictionary[key] = propagate_attributes(value)
    return dictionary

def merge_parent_attributes(dictionary, attributes):
    for key_ in list(dictionary):
        key = key_[:-1] if key_[-1] == '+' else key_
        if key != key_ and key in attributes:
            if isinstance(dictionary[key_], list):
                dictionary[key] = attributes[key] + dictionary.pop(key_)
            else:
                dictionary[key] = str(attributes[key]) + ' ' + str(dictionary.pop(key_))
    return { **attributes, **dictionary }

def queue_run_commands(level, dictionary, test_commands):
    for key, value in dictionary.items():
        if isinstance(value, dict) and key != 'test_group':
            next_level = level + key + '/'
            queue_run_commands(next_level, value, test_commands)
        elif key == 'test_group':
            test_commands += [(level, k, v['command']+' '+v['args'], v['timeout'], v['rules']) for k,v in value.items() if isinstance(v, dict)]

def get_username():
    return pwd.getpwuid(os.getuid()).pw_name

def timestamp():
    return datetime.datetime.now()

def timestamp_str():
    return timestamp().strftime("%Y-%m-%d %H:%M:%S")

def setup_session(session_db, args):

    session_db['session']['start_date'] = timestamp()
    session_db['session']['uid'] = '.'.join([session_db['session']['name'], str(get_username()),
                                             session_db['session']['start_date'].strftime("%Y-%d-%m-%H%M%S"), str(os.getpid())])
    session_db['session']['dir'] = args.dir.joinpath(session_db['session']['uid'])

    session_db['session']['dir'].mkdir(parents=True)

    session_db['session']['junit_xml'] = session_db['session']['dir'].joinpath('test-reports/junit.xml')

    session_db['session']['junit_xml'].parent.mkdir(parents=True)

    # Set defaults if not specified in session file
    session_db['session'].setdefault('jobs', 1)
    session_db['session'].setdefault('scheduler', 'rr')

    # Labels extract from cmd lines
    label_set = set(args.labels.split(',') if args.labels else [])

    session_db['session']['filters'] = dict()
    session_db['session']['filters']['group'] = args.group
    session_db['session']['filters']['labels'] = {
        'pos' : [item for item in label_set if not item.startswith('~')],
        'neg' : [item[1:] for item in label_set if item.startswith('~') and item[1:]]
    }

    session_db['session']['stats'] = {
        'prefilter' : { 'num_tests': None, 'num_runs': None},
        'postfilter' : { 'num_tests': None, 'num_runs': None },
        'postrun' : { 'exec': None, 'pass': None, 'fail': None, 'skip': None }
    }

def fmt_postrun_stats(session_db):
    return 'runs: {exec}, passed: {pass}, failed: {fail}, skipped: {skip}'.format_map(session_db['session']['stats']['postrun'])

def session_attr_args(args, session_db):
    for sect, key, is_append, value  in args.attr:
        if not sect in session_db or not key in session_db[sect]:
            print(cstr(f"Warning : illegal attribute {sect}.{key} is ignored", MAGENTA))
            continue
        attr = session_db[sect][key]
        attr_ = list(map(lambda x: convert_value(x), value.split(',')))
        if len(attr_) == 1:
            attr_ = attr_[0]
        if is_append and isinstance(attr_, (int, str, list)):
            if isinstance(attr, int):
                attr = attr + attr_
            elif isinstance(attr, str):
                attr = str(attr) + ' ' + str(attr_)
            elif isinstance(attr, list):
                attr = attr + attr_
            else:
                print(cstr(f"Warning : illegal append on {sect}.{key} attribute is ignored", MAGENTA))
        else:
            attr = attr_

        session_db[sect][key] = attr

def main():

    #Arguments Parser
    def parse_args():

        # 'attr' handling action class
        class attrAction(argparse.Action):

            def __call__(self, parser, namespace, values, option_string=None):

                # attributes are expected to be of the form <section>.<attr>[+]=<value>
                m = re.fullmatch(r"(\w+)\.(\w+)(\+?)=(.*)", values[0])
                if not m:
                    print(cstr('Warning : malformed attribute {}'.format(values[0]), MAGENTA))
                    return
                else:
                    sect, key, is_append, value = m.group(1), m.group(2), m.group(3) == '+', m.group(4)
                    getattr(namespace, self.dest).append((sect, key, is_append, value))

        parser = argparse.ArgumentParser(
            description='submit regression jobs in batch, log failure analysis and status reporting'
        )
        parser.add_argument('--dir', help='session output directory', type=pathlib.Path, required=False, default='regr/')
        parser.add_argument('--build', help='execute session build', action='store_true')
        parser.add_argument('-j', '--jobs', help='concurrent run jobs', nargs='?', const=0, type=int, default=None)
        parser.add_argument('--count', help='overidde default run count', type=int, required=False, default=None)
        parser.add_argument('--labels', type=str, help='Labels to include or exclude tests from regression', required=False, default='')
        parser.add_argument('--seq', help='sequential run scheduler', action='store_true')
        parser.add_argument('--attr', help='overwrite session attribute', nargs='+', action=attrAction, required=False, default=[])
        parser.add_argument('file', help="regression file", type=argparse.FileType('rt'))
        parser.add_argument('group', type=str, nargs='?', default='', help='Optional hierarchical group')

        if __name__ == "__main__":
            parser.prog = 'regrLauncher.py'

        return parser.parse_args()

    args = parse_args()

    #---------------------------------------------------
    # Setup
    #---------------------------------------------------

    # Session db from json file
    with args.file as file:
        session_db = json.load(file)

    # Number of concurrent jobs from command line
    if args.jobs is not None:
        session_db['session']['jobs'] = args.jobs if args.jobs > 0 else None

    # Job queuing scheduler behavior
    if args.seq:
        session_db['session']['scheduler'] = 'seq'

    # Override default count from command line
    if args.count is not None:
        session_db['run']['count'] = args.count if args.count > 0 else None

    # Set count to default if not defined in the session file
    session_db['run'].setdefault('count', 1)

    # Set seed to default if not defined in the session file
    session_db['run'].setdefault('seed', None)

    # Override session attribues from the command line
    session_attr_args(args, session_db)

    # Propagate session attributes top-down
    session_db = propagate_attributes(session_db)

    # Prepare execution based on parameters from session attributes
    setup_session(session_db, args)

    # Initialize the job queueing mechanism for execution stage
    job_queuer = rlJobQueuer(session_db)

    # Run execution queue should not be empty
    if not session_db['session']['stats']['postfilter']['num_runs']:
        print(cstr('Run session execution queue is empty', RED))
        exit(1)

    # Initialize shared database connection
    session_db['session']['db_file'] = session_db['session']['dir'].joinpath('regr.db')
    init_db(session_db['session']['db_file'])

    # Insert session record and get session_id
    sql = sqlDbSession(session_db['session']['db_file'])

    sql.insert_session(
        session_db['session']['name'],
        str(session_db['session']['dir']),
        session_db['session']['start_date'].strftime("%Y-%m-%d %H:%M:%S"),
        SESSION_STATUS_ENUM['running']
    )

    session_db['session']['id'] = sql.session_id

    #---------------------------------------------------
    # Build
    #---------------------------------------------------

    if args.build:
        print(f"Execute build session in {session_db['session']['dir']}")
        bx = sessionBuildExecutor(session_db)
        try:
            bx()
            bx.close_exec()
            print(cstr("Build session done [{}]".format(bx.get_exec_time('seconds')), GREEN))
        except Exception as e:
            bx.close_exec()
            sql.update_session(timestamp_str(), SESSION_STATUS_ENUM['finished'])
            print(e)
            print(cstr("Build session failed [{}]".format(bx.get_exec_time('seconds')), RED))
            exit(1)

    #---------------------------------------------------
    # Run
    #---------------------------------------------------

    print(f"Execute run session in {session_db['session']['dir']}")

    rx = sessionRunExecutor(session_db)

    with multiprocessing.get_context("spawn").Pool(session_db['session']['jobs']) as p:
    #with concurrent.futures.ProcessPoolExecutor(max_workers=session_db['session']['jobs']) as p:
        try:
            rx.tests_status += p.imap_unordered(rx, job_queuer.run_command_gen())
            #rx.tests_status += p.map(rx, job_queuer.run_command_gen())
        except KeyboardInterrupt:
            p.close()
            p.terminate()
            p.join()
            #p.shutdown(wait=False)

    rx.close_exec()
    exec_time = rx.get_exec_time('seconds')

    #---------------------------------------------------
    # Report
    #---------------------------------------------------

    # Generate junit.xml
    with session_db['session']['junit_xml'].open('w') as fp:
        rpt = JUnitXMLReport(session_db, rx.tests_status)
        rpt.write_junit_xml(fp)

    # Session run summary
    run_status_s = fmt_postrun_stats(session_db)

    # Update session record as finished
    sql.update_session(timestamp_str(), SESSION_STATUS_ENUM['finished'])

    # Exit Status
    if not rx.check_status():
        print(cstr(f'Run session completed with failures ({run_status_s}) [{exec_time}]', RED))
        exit(1)
    else:
        print(cstr(f'Run session completed succesfully ({run_status_s}) [{exec_time}]', GREEN))

if __name__ == "__main__":
    main()
