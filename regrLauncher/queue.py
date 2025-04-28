import fnmatch
import itertools

from .utils import cstr, MAGENTA, RED
from .utils import setenv, subst_env
from .utils import getrandom_hex, convert_value

DEFAULT_SEED_VALUE = 0
DEFAULT_RAND_SEED_SIZE = 4 # 32bit

# Create list of jobs
class rlJobQueuer:

    def __init__(self, session_db):
        self.run_commands = dict()
        self.run_id = 0
        # Recurse session run to collect run commands
        self.__recurse_session_run('/', session_db['run'], self.run_commands)
        # Pre-filter session stats
        self.__adjust_runcmd_attributes()
        self.__update_session_stats(session_db['session']['stats']['prefilter'])
        # Filter run commands based on session filters
        self.__sanitize_filters(session_db['session']['filters'])
        self.__filter_runs(session_db['session']['filters'])
        # Post-filter session stats
        self.__adjust_runcmd_attributes()
        self.__update_session_stats(session_db['session']['stats']['postfilter'])
        # Command fetch scheduler selection
        if session_db['session']['scheduler'] == 'seq':
            self.__fetch_command = self.__fetch_command_seq
        else :
            self.__fetch_command = self.__fetch_command_rr

    def run_command_gen(self):
        for key, value in self.__fetch_command():
            rl_seed = self.__get_seed_value(value['seed'])
            self.__propagate_attr_env({ 'RL_SEED' : rl_seed })
            run_cmd = (key, self.run_id, subst_env(value['command'] + ' ' + value['args']), value['timeout'], value['rules'])

            self.run_id += 1
            yield run_cmd

    def __recurse_session_run(self, hier, dictionary, run_commands):
        for key, value in dictionary.items():
            if isinstance(value, dict) and key != 'test_group':
                next_hier = hier + key + '/'
                self.__recurse_session_run(next_hier, value, run_commands)
            elif key == 'test_group':
                run_commands.update({ hier + k : v for k,v in value.items() if isinstance(v, dict)})

    # Fetch commands from table in round-robin fashion
    def __fetch_command_rr(self):
        while any(self.runcmd_count.values()):
            for key, value in self.run_commands.items():
                if self.runcmd_count[key] > 0:
                    self.runcmd_count[key] -= 1
                    # get run command seed value
                    value['seed'] = self.__get_seed_attribute(key)
                    yield (key, value)
                else:
                    continue

    # Fetch commands from table in sequential fashion
    def __fetch_command_seq(self):
        for key, value in self.run_commands.items():
            while(self.runcmd_count[key] > 0):
                self.runcmd_count[key] -= 1
                # get run command seed value
                value['seed'] = self.__get_seed_attribute(key)
                yield (key, value)

    def __sanitize_filters(self, filters_dict):
        # Flag 'group' attribute if no matching run command found
        if not ( list(filter(lambda x: x.startswith(filters_dict['group']), self.run_commands)) or
            fnmatch.filter(self.run_commands, filters_dict['group']) ) :
            print(cstr("Warning : invalid group attribute : {}".format(filters_dict['group']), MAGENTA))
        # Remove invalid labels
        valid_labels = set(itertools.chain(*[self.run_commands[key]['labels'] for key in self.run_commands]))
        invalid_labels = set(filters_dict['labels']['pos'] + filters_dict['labels']['neg']).difference(valid_labels)
        if invalid_labels:
            print(cstr("Warning : ignored invalid labels : {}".format(', '.join(invalid_labels)), MAGENTA))
        filters_dict['labels']['pos'] = set(filters_dict['labels']['pos']).difference(invalid_labels)
        filters_dict['labels']['neg'] = set(filters_dict['labels']['neg']).difference(invalid_labels)

    # Filter runs based on session attributes defined in 'filters' dict
    def __filter_runs(self, filters_dict):
        # first, filter command list based on 'group' attribute
        hier_def = filters_dict['group']
        self.run_commands = {
            key: val for key, val in self.run_commands.items()
            if not hier_def or key.startswith(hier_def) or fnmatch.fnmatch(key, hier_def)
        }
        # then, further filter run commands list based on 'labels' pos/neg attributes
        labels_p = filters_dict['labels']['pos']
        labels_n = filters_dict['labels']['neg']
        self.run_commands = {
            key: val for key, val in self.run_commands.items()
            if (not labels_p or labels_p <= set(val['labels'])) and labels_n.isdisjoint(set(val['labels']))
        }

    def __update_session_stats(self, stats_dict):
        stats_dict['num_tests'] = len(self.run_commands)
        stats_dict['num_runs'] = sum(self.runcmd_count.values())

    def __adjust_runcmd_attributes(self):
        copy_object = lambda v : v.copy() if isinstance(v, list) else v
        # Populate run command iterative attributes
        self.runcmd_count = dict()
        self.runcmd_count.update({k : int(v['count']) if v['count'] != None else None for k,v in self.run_commands.items()})
        self.runcmd_seed = dict()
        self.runcmd_seed.update({k : copy_object(v['seed']) for k,v in self.run_commands.items()})
        # Align count and seed attributes per guideline
        for key in self.runcmd_count.keys():
            # If seed is a single element, skip update attributes
            if not isinstance(self.runcmd_seed[key], list):
                continue
            count, num_seeds = self.runcmd_count[key], len(self.runcmd_seed[key])
            # If count is None, set count to number of seeds in the list
            if count == None:
                self.runcmd_count[key] = num_seeds
            # If count greater than number of seeds, align count to number of seeds
            elif count > num_seeds:
                self.runcmd_count[key] = num_seeds
            # If count smaller than number of seeds, align seed list to count
            elif count < num_seeds:
                self.runcmd_seed[key] = self.runcmd_seed[key][0:count]
            else: # count == num_seeds, nothing to align
                continue
        # delete the tests commands that have count = 0
        rm_keys = [ key for key, value in self.runcmd_count.items() if not value ]
        for key in rm_keys:
            del self.run_commands[key]
            del self.runcmd_count[key]
            del self.runcmd_seed[key]

    def __propagate_attr_env(self, attributes):
        for key, value in attributes.items():
            setenv(key, value)

    def __get_seed_value(self, seed_attr):
        if seed_attr == None:
            return int(DEFAULT_SEED_VALUE);
        elif seed_attr == 'random':
            return getrandom_hex(DEFAULT_RAND_SEED_SIZE)
        else:
            return convert_value(seed_attr)

    def __get_seed_attribute(self, cmd_key):
        if isinstance(self.runcmd_seed[cmd_key], list):
            return self.runcmd_seed[cmd_key].pop(0)
        else:
            return self.runcmd_seed[cmd_key]
