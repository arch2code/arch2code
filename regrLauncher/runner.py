import subprocess
import shlex
import os
import json
import re
import datetime
import time

from .time import timedelta
from .utils import cstr, RED, GREEN
from .utils import _str_join

from .database import sqlDbRun

''' Clean up output from subprocess.CalledProcessError.__str__() '''
class CalledProcessError(subprocess.CalledProcessError):

    @classmethod
    def downcast(cls, baseobj):
        return cls(baseobj.returncode, _str_join(baseobj.cmd), baseobj.output, baseobj.stderr)

''' Clean up output from subprocess.TimeoutExpired.__str__() '''
class TimeoutExpired(subprocess.TimeoutExpired):

    @classmethod
    def downcast(cls, baseobj):
        return cls(_str_join(baseobj.cmd), '{:.0f}'.format(baseobj.timeout), baseobj.output, baseobj.stderr)

class sessionExecStatus(object):

    def __init__(self, status):

        if isinstance(status, subprocess.CompletedProcess):
            self.type = "CompletedProcess"
            self.returncode = status.returncode
            self.output = status.stdout
            self.stderr = status.stderr
            self.str = status.__repr__()
        elif isinstance(status, subprocess.CalledProcessError):
            status = CalledProcessError.downcast(status)
            self.type = "CalledProcessError"
            self.returncode = status.returncode
            self.output = status.output
            self.stderr = status.stderr
            self.str = status.__str__()
        elif isinstance(status, subprocess.TimeoutExpired):
            status = TimeoutExpired.downcast(status)
            self.type = "TimeoutExpired"
            self.returncode = None
            self.timeout = status.timeout
            self.output = status.output
            self.stderr = status.stderr
            self.str = status.__str__()
        elif isinstance(status, FileNotFoundError):
            self.type = "ExecFileNotFound"
            self.returncode = None
            self.output = ''
            self.stderr = ''
            self.str = status.__str__()

    def set_runtime(self, dtime):
        self.runtime = datetime.timedelta(seconds=dtime)

    def __str__(self):
        return self.str

    # Returns 'false' when execution status is exception
    def __bool__(self):
        if self.type in ['CalledProcessError', 'TimeoutExpired', 'ExecFileNotFound'] :
            return False
        else:
            return True

class sessionExecutorBase:

    def __init__(self, session_db):
        self.session_db = session_db
        self.__session_done = False
        self.__init_ts = time.time()

    def execute_command(self, command, fp, timeout, env):
        ts = time.time()
        try:
            stat = sessionExecStatus(
                subprocess.run(shlex.split(command), shell=False, check=True, stdout=fp, stderr=fp, timeout=timeout, env=env)
            )
        except subprocess.CalledProcessError as e:
            stat = sessionExecStatus(e)
        except subprocess.TimeoutExpired as e:
            stat = sessionExecStatus(e)
        except FileNotFoundError as e:
            stat = sessionExecStatus(e)
        stat.set_runtime(time.time()-ts)
        return stat

    # Terminate execution
    def close_exec(self):
        self.__session_done = True
        self.__done_ts = time.time()

    def get_exec_time(self, precision = 'seconds'):
        assert(self.__session_done) # user must close exec before calling this method
        return timedelta(seconds=self.__done_ts - self.__init_ts, precision=precision)

class sessionBuildExecutor(sessionExecutorBase):

    def __call__(self):
        log_ = self.session_db['session']['dir'].joinpath("build.log")
        cmd, timeout = (self.session_db['build']['command'], self.session_db['build']['timeout'])
        with open(log_, 'wt') as fp:
            self.exec_status = self.execute_command(cmd, fp, timeout, env=None)
            if not self.exec_status or self.exec_status.returncode:
                raise RuntimeError(self.exec_status)

class sessionRunExecutor(sessionExecutorBase):

    def __init__(self, session_db):
        super().__init__(session_db)
        self.tests_status = list()

    def __call__(self, test_cmd):
        sql = sqlDbRun(self.session_db['session']['db_file'], self.session_db['session']['id'])
        hier_test, rid, cmd, timeout, rules = test_cmd
        hier, test = os.path.split(hier_test)
        run_id = f"run_{rid}"
        print("Running '{}/{}' ...".format(hier_test, run_id), flush=True)
        rundir = self.session_db['session']['dir'].joinpath('runs' + hier_test + '/' + run_id)
        rundir.mkdir(parents=True)
        rundir_symlink = self.session_db['session']['dir'].joinpath('runs' + '/' + run_id)
        rundir_symlink.symlink_to('.' + hier_test + '/' + run_id)
        cmd_ = rundir.joinpath(test+'.cmd')
        with open(cmd_, 'wt') as fp:
            fp.write('# ' + str(hier_test) + '\n')
            fp.write(str(cmd)+'\n')
        log_ = rundir.joinpath(test+'.log')

        # Insert run record and get id
        rowid = sql.insert_run(run_id, hier, test, str(rundir), str(cmd))

        with open(log_, 'wt') as fp:
            exec_status = self.execute_command(cmd, fp, timeout, env=None)

        # Log Parse Analyzer
        lpa = logParserAnalyzer(rules)
        failures = lpa.analyze(log_)

        test_status = sessionTestStatus(test_cmd, exec_status, failures)

        # Update run record with test status once completed
        sql.update_run(run_id,
            int(bool(exec_status)), len(failures), exec_status.runtime.total_seconds(), int(bool(exec_status))
        )

        # Apply log retention policy
        self.__lrp(log_, bool(test_status))

        print("Running '{}/{}' done [{}] ({})".format(hier_test, run_id,
            timedelta.downcast(exec_status.runtime, 'hundredths'), cstr('PASS', GREEN) if test_status else cstr('FAIL', RED)), flush=True)

        return test_status

    # Returns 'false' is any of the test has failed status
    def check_status(self):
        if list(filter(lambda ts: not ts, self.tests_status)):
            return False
        else:
            return True

    # Terminate execution
    def close_exec(self):
        super().close_exec()
        self.__update_session_stats(self.session_db['session']['stats']['postrun'])

    def __update_session_stats(self, stats_dict):
        stats_dict['exec'] = len(self.tests_status)
        stats_dict['fail'] = sum(map(lambda ts: not bool(ts), self.tests_status))
        stats_dict['pass'] = sum(map(lambda ts: bool(ts), self.tests_status))
        stats_dict['skip'] = self.session_db['session']['stats']['postfilter']['num_runs'] - stats_dict['exec']

    def __lrp(self, logfile, test_status):
        def sp_compress_file(filename):
            subprocess.run(["gzip", filename], check=False)

        match (self.session_db['session']['lrp'], test_status):
            case (1, True ) | (2, _) | (3, True): logfile.unlink()
            case (3, False) | (4, _): sp_compress_file(str(logfile))
            case _: pass

class sessionTestStatus(object):

    def __init__(self, run_cmd, exec_status, log_failures):
        self.run_cmd = run_cmd
        self.exec_status = exec_status
        self.log_failures = log_failures

    def log_failures_status(self, level='error'):
        sevset = set([item['sev'] for item in self.log_failures])
        match level:
            case 'info':
                return not sevset.isdisjoint(['info', 'warning', 'error', 'fatal'])
            case 'warning':
                return not sevset.isdisjoint(['warning', 'error', 'fatal'])
            case 'error':
                return not sevset.isdisjoint(['error', 'fatal'])
            case 'fatal':
                return not sevset.isdisjoint(['fatal'])
            case _:
                return True

    # Returns 'false' if failures in execution or log analysis
    def __bool__(self):
        if not self.exec_status or self.log_failures_status(level='error'):
            return False
        else :
            return True

    def __repr__(self):
        body = ', '.join([str(self.run_cmd), str(self.exec_status), str(self.log_failures)])
        return "{}({})".format(type(self).__name__, body)

class logParserAnalyzer:

    def __init__(self, rules_files):
        self.rulesets = dict()
        self.filters = dict()
        self.modifiers = dict()
        for file in rules_files:
            with open(file, 'rt') as fp:
                ruleset= json.load(fp)
                self.rulesets[ruleset['name']] = ruleset
        for _, rulesets in self.rulesets.items():
            for fname, fdef in rulesets['filters'].items():
                self.filters[fname] = fdef
                if fname in rulesets['modifiers']:
                    if fname not in self.modifiers:
                        self.modifiers[fname] = rulesets['modifiers'][fname]
                    else:
                        self.modifiers[fname].update(rulesets['modifiers'][fname])

    def analyze(self, logfile):
        fl = list()
        with open(logfile) as fp:
            buffer = fp.read()
            for fname, fdef in self.filters.items():
                re_pat, msg_pat, file_pat = r'{}'.format(fdef['re']), fdef['msg'], fdef['file']
                lineno, mpos = (1, 0)
                for m in re.finditer(re_pat, buffer, re.MULTILINE):
                    msg = m.expand(msg_pat)
                    file = m.expand(file_pat) if file_pat else None
                    lineno += buffer[mpos:mpos+m.start()].count('\n');
                    mpos += m.start()
                    failure = { 'name' : fname, 'sev' : fdef['sev'], 'msg' : msg, 'file' : file, 'lineno' : lineno }
                    self.__failure_modifier(failure)
                    fl.append(failure)
        return fl

    def __failure_modifier(self, failure):
        fname = failure['name']
        msg = failure['msg']
        if fname not in self.modifiers:
            return
        for _, fdef in self.modifiers[fname].items():
            re_pat, msg_pat = r'{}'.format(fdef['re']), r'{}'.format(fdef['msg'])
            p = re.compile(re_pat)
            msg = p.sub(msg_pat, msg)
        failure['msg'] = msg
        return
