"""Create a standalone, design-only HTML preview with fictional SAMPLE data.
Not part of the live app; use the Flask website for functional actions.
"""
from pathlib import Path
from types import SimpleNamespace
from jinja2 import Environment, FileSystemLoader
import base64

root=Path(__file__).resolve().parent.parent
src=root/'campusvote'
env=Environment(loader=FileSystemLoader(src/'templates'), autoescape=True)

def url_for(endpoint,**kwargs):
    return str(src/'static'/kwargs['filename']) if endpoint=='static' else '#'

def fmt_time(date):
    return '18 Nov 2026, 10:30 AM IST' if date else '—'

env.globals.update(url_for=url_for,csrf_token=lambda:'sample',request=SimpleNamespace(args={}),
                   get_flashed_messages=lambda **kwargs:[],election_state=lambda e:e['state'] if 'state' in e else e['status'])
env.filters.update(ist=fmt_time,ist_input=lambda x:x)
counts=dict(students=1660,approved=1480,pending=26,elections=7,open=3,voted=267,turnout=80,chart_peak=56)
example=[('Arts Council',33,42),('Library Board',25,40),('Sports Union',28,40),
         ('Cultural Club',56,65),('Tech Society',32,50),('Student Council',48,60),('Eco Committee',45,50)]
elections=[dict(id=i+1,title=title,cast_votes=v,eligible=eligible,bar_height=round(100*v/56),
                turnout=round(v/eligible*100),starts_at='2026-11-18T05:00:00Z',state='open' if i%3==0 else 'scheduled',
                status='scheduled',created_at='2026-11-18T05:00:00Z') for i,(title,v,eligible) in enumerate(example)]
pending=[dict(full_name=n,student_id=f'STU-{i:03}') for i,n in enumerate(('Ethan Clarke','Ava Mitchell','Liam Parker'),1)]
activity=[dict(event_type=e,created_at='2026-11-18T05:00:00Z') for e in ('student_approved','election_scheduled','candidate_added')]
context=dict(page='dashboard',current_user=dict(role='admin',full_name='Campus Administrator',student_id='ADM001',approval_status='approved'),
             counts=counts,elections=elections,pending=pending,activity=activity)
css=(src/'static/css/main.css').read_text(encoding='utf-8')
js=(src/'static/js/main.js').read_text(encoding='utf-8')
icons=(src/'static/images/icons.svg').read_text(encoding='utf-8')
icon_defs=icons[icons.find('>')+1:icons.rfind('</svg>')]
logo=base64.b64encode((src/'static/images/logo.svg').read_bytes()).decode('ascii')

def export(template, context, out_name, caption):
    html=env.get_template(template).render(**context)
    html=html.replace(f'<link rel="stylesheet" href="{src}/static/css/main.css">', '<style>'+css+'</style>')
    html=html.replace(f'<script src="{src}/static/js/main.js" defer></script>', '')
    html=html.replace(f'{src}/static/images/icons.svg#','#')
    html=html.replace(f'{src}/static/images/logo.svg','data:image/svg+xml;base64,'+logo)
    html=html.replace('<body class="app-page">', '<body class="app-page"><svg xmlns="http://www.w3.org/2000/svg" style="position:absolute;width:0;height:0;overflow:hidden" aria-hidden="true">'+icon_defs+'</svg>')
    html=html.replace('</body></html>', '<script>'+js+'</script></body></html>')
    html=html.replace('<title>'+('Admin dashboard' if 'admin' in template else 'Student dashboard')+' · CampusVote</title>',
                      '<title>'+caption+' (fictional preview numbers)</title>')
    out=root.parent/out_name
    out.write_text(html,encoding='utf-8')
    print('Standalone UI preview:',out)

export('admin/dashboard.html',context,'CampusVote_UI_Preview.html','CampusVote Admin Dashboard')
student_elections=[
 dict(id=1,title='Student Council Election',description='Elect the next student council president.',state='open',status='scheduled',candidate_count=3,receipt=None,starts_at='2026-11-18T05:00:00Z',ends_at='2026-11-20T05:00:00Z'),
 dict(id=2,title='Tech Club Leadership',description='Choose the technology club committee.',state='scheduled',status='scheduled',candidate_count=3,receipt=None,starts_at='2026-11-22T05:00:00Z',ends_at='2026-11-25T05:00:00Z'),
 dict(id=3,title='Cultural Committee 2026',description='Annual campus cultural committee election.',state='published',status='published',candidate_count=3,receipt='fictional-example-receipt',starts_at='2026-11-01T05:00:00Z',ends_at='2026-11-04T05:00:00Z'),
]
student_context=dict(page='dashboard',current_user=dict(role='student',full_name='Ava Mitchell',student_id='STU001',approval_status='approved'),
                     elections=student_elections,stats=dict(total=3,open=1,voted=1,upcoming=1),published=[student_elections[-1]])
export('student/dashboard.html',student_context,'CampusVote_Student_UI_Preview.html','CampusVote Student Dashboard')

vote_candidates=[
    dict(id=101,full_name='Riya Sharma',department='CSE · 3rd Year',manifesto='Transparent campus events, improved student support and more academic opportunities.'),
    dict(id=102,full_name='Karan Patel',department='ECE · 3rd Year',manifesto='Better access to technical clubs, workshops and a stronger campus community.'),
    dict(id=103,full_name='Neha Rao',department='IT · 2nd Year',manifesto='Clear communication, inclusive events and student-focused learning resources.')
]
vote_context=dict(page='elections',current_user=dict(role='student',full_name='Ava Mitchell',student_id='STU001',approval_status='approved'),
                  e=dict(id=1,title='Student Council Election',description='Choose the next student council representative.',
                         status='scheduled',receipt=None,starts_at='2026-11-18T05:00:00Z',ends_at='2026-11-20T05:00:00Z'),
                  state='open',candidates=vote_candidates)
export('student/vote.html',vote_context,'CampusVote_Voting_UI_Preview.html','CampusVote Candidate Voting Screen')
