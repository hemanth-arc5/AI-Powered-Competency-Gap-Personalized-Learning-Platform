import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import date
from modules.scoring import load_competencies, load_questions, load_role_question_bank, get_role_competencies, get_questions_for_skills
from modules.gap_analysis import generate_gap_report
from modules.ai_service import generate_learning_plan, generate_practice_questions
from modules.recommendations import load_resources, recommend_resources
from modules.analytics import build_gap_table, improvement_summary
from modules.storage import save_task, update_task_status, load_tasks, save_assessment, load_assessments
from utils.session import init_state, reset_demo, logout
from utils.auth import register, authenticate
from utils.ui import apply_styles, page_header, metric_card

ROOT = Path(__file__).resolve().parent
COMPETENCIES = load_competencies(ROOT / "data" / "competencies.csv")
QUESTIONS_DIR = ROOT / "data" / "questions"
QUESTIONS = [q for file in sorted(QUESTIONS_DIR.glob("*.csv")) for q in load_questions(file)] if QUESTIONS_DIR.exists() else load_questions(ROOT / "data" / "questions.csv")
RESOURCES = load_resources(ROOT / "data" / "resources.csv")
ROLES = list(dict.fromkeys(c["role"] for c in COMPETENCIES))
PAGES = ["Home", "Student Profile", "Select Goal", "Assessment", "Gap Analysis", "Learning Plan", "Practice Quiz", "Progress"]

st.set_page_config(page_title="SkillPath AI", page_icon="🎓", layout="wide")
apply_styles()
init_state()
# Additional integration state
for key, default in {"role": ROLES[0], "gap_report": None, "ai_plan": None, "practice_questions": [], "practice_skill": None, "practice_score": None, "quiz_generation": 0}.items():
    if key not in st.session_state: st.session_state[key] = default

def go(page, message=None):
    st.session_state.goto = page
    if message: st.session_state.flash = message
    st.rerun()

if "goto" in st.session_state:
    st.session_state.nav = st.session_state.pop("goto")
if "nav" not in st.session_state: st.session_state.nav = "Home"

def login_page():
    st.markdown("<style>[data-testid='stSidebar'],[data-testid='collapsedControl']{display:none}</style>", unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 1.4, 1])
    with mid:
        st.markdown("# 🎓 SkillPath AI")
        st.markdown("AI-Powered Competency Gap & Personalized Learning Platform")
        t1,t2=st.tabs(["Login","Create account"])
        with t1:
            with st.form("login_form"):
                u=st.text_input("Username"); p=st.text_input("Password",type="password")
                submit=st.form_submit_button("Login",type="primary")
            if submit:
                user=authenticate(u,p)
                if user: do_login(user,"Welcome back!")
                else: st.error("Invalid username or password.")
        with t2:
            with st.form("signup_form"):
                n=st.text_input("Full name"); su=st.text_input("Choose username"); em=st.text_input("Email (optional)")
                p1=st.text_input("Password",type="password"); p2=st.text_input("Confirm password",type="password")
                submit=st.form_submit_button("Create account",type="primary")
            if submit:
                ok,msg=register(su,n,em,p1,p2)
                if ok: do_login({"username":su.strip().lower(),"name":n.strip(),"email":em.strip()},"Account created.")
                else: st.error(msg)

def do_login(user,msg):
    st.session_state.user=user
    st.session_state.profile["name"]=user["name"]
    st.session_state.profile["email"]=user["email"]
    go("Student Profile",msg)

if "user" not in st.session_state:
    login_page(); st.stop()

with st.sidebar:
    st.markdown("## 🎓 SkillPath AI")
    page=st.radio("Navigation",PAGES,key="nav")
    st.divider()
    st.caption("Signed in as: "+st.session_state.user["name"])
    if st.button("Logout"):
        logout(); st.rerun()
    if st.button("Reset demo session"):
        reset_demo()
        for key in ["gap_report","ai_plan","practice_questions","practice_skill","practice_score"]:
            st.session_state[key]=None if key in ["gap_report","ai_plan","practice_skill","practice_score"] else []
        st.rerun()

def header(title,subtitle):
    page_header(title,subtitle)
    if "flash" in st.session_state: st.success(st.session_state.pop("flash"))

def current_student():
    return st.session_state.user.get("username","student")

def role_questions(role):
    comps=get_role_competencies(COMPETENCIES,role)
    role_bank = load_role_question_bank(QUESTIONS_DIR, role)
    return comps, role_bank

def scores_for_ai(report):
    return [{"skill_id":r["skill_id"],"skill_name":r["skill_name"],"current":r["current"],
             "target":r["target"],"gap":r["gap"] or 0,"priority":r["priority"]}
            for r in report["rows"]]

def resources_for_ai():
    items=RESOURCES.to_dict(orient="records")
    for x in items:
        try:
            d=str(x.get("duration",""))
            x["duration"]=int(float(d.split()[0])*60) if "hour" in d.lower() else int(float(d.split()[0]))
        except Exception: x["duration"]=120
    return items

if page=="Home":
    header("Welcome to SkillPath AI","Assess your skills, find gaps, and follow a personalized learning roadmap.")
    a,b,c=st.columns(3)
    with a: metric_card("Learner",st.session_state.profile["name"] or "Not set","Profile")
    with b: metric_card("Learning goal",st.session_state.goal or "Not selected","Target")
    with c: metric_card("Assessment","Completed" if st.session_state.gap_report else "Pending","Competency check")
    st.markdown("### Learning journey")
    st.write("**1. Profile → 2. Select role → 3. Assessment → 4. Gap analysis → 5. Learning plan → 6. Practice → 7. Progress**")
    st.info("Start by completing your profile and selecting a target role.")
    if st.button("Get started",type="primary"): go("Student Profile")

elif page=="Student Profile":
    header("Student Profile","Set up your learner profile.")
    p=st.session_state.profile
    with st.form("profile_form"):
        name=st.text_input("Name",p["name"]); email=st.text_input("Email (optional)",p["email"])
        level=st.selectbox("Current level",["Beginner","Intermediate","Advanced"],index=["Beginner","Intermediate","Advanced"].index(p["level"]))
        field=st.selectbox("Area of study",["Computer Science","Data Science","Web Development","Business","Other"],index=["Computer Science","Data Science","Web Development","Business","Other"].index(p["field"]))
        save=st.form_submit_button("Save profile",type="primary")
    if save:
        if not name.strip(): st.error("Please enter your name.")
        elif email and ("@" not in email): st.error("Please enter a valid email.")
        else:
            st.session_state.profile={"name":name.strip(),"email":email.strip(),"level":level,"field":field}
            go("Select Goal","Profile saved.")

elif page=="Select Goal":
    header("Select Learning Goal","Choose the role whose competencies you want to assess.")
    role=st.selectbox("Target role",ROLES,index=ROLES.index(st.session_state.role) if st.session_state.role in ROLES else 0)
    comps=get_role_competencies(COMPETENCIES,role)
    st.write("Competencies included:")
    st.dataframe(pd.DataFrame([{"Skill":c["skill_name"],"Target score":c["target_score"],"Prerequisites":", ".join(c["prerequisites"]) or "None"} for c in comps]),hide_index=True,width="stretch")
    hours=st.slider("Available study hours per week",1,20,5)
    if st.button("Save goal",type="primary"):
        st.session_state.role=role; st.session_state.goal=role; st.session_state.hours_per_week=hours
        st.session_state.gap_report=None; st.session_state.ai_plan=None
        go("Assessment","Goal saved. Take the diagnostic assessment.")

elif page=="Assessment":
    header("Diagnostic Assessment","Answer the questions. Scores are calculated from your answers, not by AI.")
    if not st.session_state.goal: st.warning("Choose a goal first.")
    else:
        comps,qs=role_questions(st.session_state.role)
        with st.form("diagnostic"):
            answers={}
            for q in qs:
                st.markdown(f"**{q['skill_id']} · {q['difficulty'].title()}**")
                selected=st.radio(q["question"],["Select an answer"]+q["options"],key="diag_"+q["question_id"])
                if selected!="Select an answer":
                    answers[q["question_id"]]=q["options"].index(selected)
            submitted=st.form_submit_button("Submit assessment",type="primary")
        if submitted:
            if len(answers)!=len(qs): st.error("Please answer every question.")
            else:
                submission={qid:"ABCD"[index] for qid,index in answers.items()}
                report=generate_gap_report(st.session_state.role,submission,QUESTIONS,COMPETENCIES)
                if report["valid"]:
                    st.session_state.gap_report=report; st.session_state.ai_plan=None
                    # Persist each assessed competency
                    for row in report["rows"]:
                        if row["current"] is not None:
                            save_assessment({"student_id":current_student(),"attempt_id":date.today().isoformat(),
                                "skill_id":row["skill_id"],"correct_count":report["skill_scores"][row["skill_id"]]["correct_count"],
                                "total_count":report["skill_scores"][row["skill_id"]]["total_count"],
                                "score":row["current"],"date":date.today().isoformat()})
                    go("Gap Analysis","Assessment scored successfully.")
                else: st.error(" ".join(report["errors"]))

elif page=="Gap Analysis":
    header("Competency Gap Analysis","Compare your current score with the target for each skill.")
    report=st.session_state.gap_report
    if not report: st.info("Complete the diagnostic assessment first.")
    else:
        rows=report["rows"]
        df=pd.DataFrame(rows)
        st.dataframe(df[["skill_name","current","target","gap","priority","status","learn_first"]].rename(columns={"skill_name":"Skill","current":"Current","target":"Target","gap":"Gap","priority":"Priority","status":"Status","learn_first":"Learn first"}),hide_index=True,width="stretch")
        if report["summary"]:
            a,b,c=st.columns(3)
            a.metric("High priority",report["summary"]["counts"]["High"])
            b.metric("Strong skills",report["summary"]["counts"]["Strong"])
            c.metric("Not assessed",len(report["summary"]["not_assessed"]))
        st.bar_chart(df.set_index("skill_name")[["current","target"]].fillna(0))
        st.write("Gap formula: **max(0, Target − Current)**. Unassessed skills are not treated as zero.")
        if st.button("Generate my learning plan",type="primary"): go("Learning Plan")

elif page=="Learning Plan":
    header("Personalized Learning Plan","AI creates a plan using the verified scores, gaps, resources and your weekly study time.")
    report=st.session_state.gap_report
    if not report: st.info("Complete assessment first.")
    else:
        hours=st.session_state.get("hours_per_week",5)
        if st.button("Generate / Regenerate plan",type="primary"):
            result=generate_learning_plan(st.session_state.role,hours,scores_for_ai(report),resources_for_ai(),
                {c["skill_id"]:c["prerequisites"] for c in get_role_competencies(COMPETENCIES,st.session_state.role)})
            st.session_state.ai_plan=result
        result=st.session_state.ai_plan
        if result:
            data=result["data"]
            if result.get("error"): st.warning("AI fallback used: "+result["error"])
            if data:
                st.success("Plan source: "+str(result.get("source")))
                st.write(data.get("summary",""))
                for w in data.get("weeks",[]):
                    with st.expander(f"Week {w.get('week')}: {w.get('topic')}",expanded=True):
                        st.write("**Objective:**",w.get("objective"))
                        st.write("**Activity:**",w.get("activity"))
                        st.write("**Checkpoint:**",w.get("checkpoint"))
                        st.write("**Estimated time:**",w.get("estimated_minutes"),"minutes")
                        rid=w.get("resource_id")
                        if rid:
                            resource=next((r for r in RESOURCES.to_dict("records") if r["resource_id"]==rid),None)
                            if resource: st.markdown(f"[{resource['title']}]({resource['url']})")
                st.caption(data.get("disclaimer","Verify resources and AI recommendations."))
        if report:
            rec=recommend_resources(pd.DataFrame(report["rows"]),RESOURCES,
                {c["skill_id"]:c["prerequisites"] for c in get_role_competencies(COMPETENCIES,st.session_state.role)})
            st.subheader("Curated resources for your gaps")
            if rec.empty: st.success("No outstanding gaps or matching recommendations.")
            else:
                for _,r in rec.iterrows():
                    st.markdown(f"**{r['priority']} · {r['skill_name']}** — {r['title']}")
                    if r["url"]: st.markdown(f"[Open resource]({r['url']}) · {r['level']} · {r['duration']}")

elif page=="Practice Quiz":
    header("AI Practice Quiz","Generate practice questions for a selected competency. If AI is unavailable, use the local question bank.")
    report=st.session_state.gap_report
    if not report: st.info("Complete the diagnostic assessment first.")
    else:
        skill_names={r["skill_id"]:r["skill_name"] for r in report["rows"]}
        skill_id=st.selectbox("Skill",list(skill_names),format_func=lambda x:skill_names[x])
        difficulty=st.selectbox("Difficulty",["easy","medium","hard"])
        n=st.slider("Number of questions",1,5,3)
        if st.button("Generate quiz"):
            ai=generate_practice_questions(skill_names[skill_id],difficulty,n,st.session_state.role)
            qs=ai["data"]["questions"] if ai["ok"] else []
            if not qs:
                bank=[q for q in get_questions_for_skills(QUESTIONS,[skill_id]) if q["difficulty"]==difficulty]
                if not bank: bank=get_questions_for_skills(QUESTIONS,[skill_id])
                qs=[{"question":q["question"],"options":q["options"],"correct_answer":q["options"][ord(q["correct_answer"])-65],"explanation":q["explanation"]} for q in bank[:n]]
                st.session_state.quiz_source="Local question bank"
                if ai["error"]: st.warning("AI unavailable; using local questions. "+ai["error"])
                if not qs: st.error("No questions available for this skill.")
            else: st.session_state.quiz_source="AI generated"
            st.session_state.practice_questions=qs; st.session_state.practice_skill=skill_id; st.session_state.practice_score=None; st.session_state.quiz_generation += 1
        qs=st.session_state.practice_questions
        if qs and st.session_state.practice_skill==skill_id:
            st.caption("Source: "+st.session_state.get("quiz_source",""))
            with st.form("practice_submit"):
                chosen=[]
                for i,q in enumerate(qs):
                    chosen.append(st.radio(q["question"],["Choose"]+q["options"],key=f"pr_{st.session_state.quiz_generation}_{skill_id}_{i}"))
                submit=st.form_submit_button("Submit quiz")
            if submit:
                if any(x=="Choose" for x in chosen): st.error("Answer every question.")
                else:
                    score=sum(x==q["correct_answer"] for x,q in zip(chosen,qs))
                    st.session_state.practice_score=round(score/len(qs)*100)
                    st.success(f"Score: {score}/{len(qs)} ({st.session_state.practice_score}%)")
                    for q,x in zip(qs,chosen):
                        st.write("Correct" if x==q["correct_answer"] else "Incorrect", "—",q["explanation"])
                    save_assessment({"student_id":current_student(),"attempt_id":date.today().isoformat()+"-quiz",
                        "skill_id":skill_id,"correct_count":score,"total_count":len(qs),"score":st.session_state.practice_score,"date":date.today().isoformat()})

elif page=="Progress":
    header("Progress & Task Tracking","Track learning tasks and compare assessment attempts.")
    tasks=load_tasks()
    with st.form("new_task"):
        a,b,c=st.columns(3)
        task_id=a.text_input("Task ID"); skill=b.selectbox("Skill ID",[x["skill_id"] for x in COMPETENCIES]); week=c.number_input("Week",1,12,1)
        title=st.text_input("Task title",value="Complete a learning resource")
        d,e=st.columns(2); resource_id=d.text_input("Resource ID",value=""); duration=e.text_input("Duration",value="1 hour")
        save=st.form_submit_button("Add task")
    if save:
        if not task_id.strip(): st.error("Task ID is required.")
        else:
            save_task({"task_id":task_id,"student_id":current_student(),"skill_id":skill,"week":week,"title":title,"resource_id":resource_id,"duration":duration,"status":"Pending"})
            st.success("Task added."); st.rerun()
    tasks=load_tasks()
    if not tasks.empty:
        st.dataframe(tasks,hide_index=True,width="stretch")
        selected=st.selectbox("Task to update",tasks.task_id.astype(str).tolist())
        status=st.selectbox("Status",["Pending","In Progress","Completed"])
        if st.button("Update task"):
            update_task_status(selected,status); st.success("Updated."); st.rerun()
        st.metric("Completed tasks",int((tasks.status=="Completed").sum()),f"of {len(tasks)}")
    assessments=load_assessments()
    if not assessments.empty:
        st.subheader("Assessment history")
        st.dataframe(assessments,hide_index=True,width="stretch")
        hist=improvement_summary(assessments)
        skill=st.selectbox("Skill progress",sorted(hist.skill_id.unique()))
        st.line_chart(hist[hist.skill_id==skill].set_index("date")[["score"]])
    if st.session_state.gap_report:
        st.subheader("Current vs target")
        df=pd.DataFrame(st.session_state.gap_report["rows"])
        st.bar_chart(df.set_index("skill_name")[["current","target"]].fillna(0))
