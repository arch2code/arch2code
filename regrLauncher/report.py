import junit_xml

class JUnitXMLReport:

    def __init__(self, session_db, tests_status):
        self.session_db = session_db
        self.testcases = list()
        for tc in tests_status:
            self.testcases.append(self.create_testcase(tc))
        self.testsuite = junit_xml.TestSuite(
            name=session_db['session']['name'],
            test_cases = self.testcases
        )

    @staticmethod
    def create_testcase(test_status):
        hier_test, rid, cmd, timeout, rules = test_status.run_cmd
        run_id = f"run_{rid}"
        tc = junit_xml.TestCase(name=run_id,
            classname=hier_test,
            elapsed_sec=test_status.exec_status.runtime.total_seconds(),
            stdout=test_status.exec_status.output,
            stderr=test_status.exec_status.stderr,
            allow_multiple_subelements=False)
        if not test_status:
            fmsg = lambda f: "[{name}] {msg} ({file})".format_map(f) if f['file'] else "[{name}] {msg}".format_map(f)
            # log based failures first
            if test_status.log_failures_status(level='error'):
                for item in filter(lambda f: f['sev'] in ['error', 'fatal'], test_status.log_failures):
                    tc.add_failure_info(message=fmsg(item), failure_type=item['sev'])
                    break # Report first failure only in junit xml (no multiple sub-elements)
            elif not test_status.exec_status:
                tc.add_error_info(
                    message="Test execution error",
                    error_type=test_status.exec_status.type,
                    output=str(test_status.exec_status)
                )
        return tc

    def write_junit_xml(self, fp):
        junit_xml.to_xml_report_file(fp, [ self.testsuite ], prettyprint=True)
