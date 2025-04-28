#!/usr/bin/env python3
from jira import JIRA

webAddress = 'https://arch2code.atlassian.net/browse/A2C-119'
webAddress = 'https://arch2code.atlassian.net'
browse = webAddress + '/browse/'

a2c = JIRA(webAddress)

out  = '[cols="8%,8%,10%,10%,64%"]\n'
out += '|===\n'
out += '|Issue|Issue Type|Priority|Status|Summary\n\n'
for issue in a2c.search_issues('resolution = Unresolved ORDER BY status ASC, priority DESC, created DESC'):
    out += f""
    out += f'|{browse}{issue.key}[{issue.key}]\n|{issue.fields.issuetype}\n|{issue.fields.priority}\n|{issue.fields.status}\n|{issue.fields.summary}\n\n'
out += '|===\n'
print(out)