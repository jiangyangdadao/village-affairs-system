"""生成演示用假数据（本地查看效果用，非生产）。

用法：在 backend 目录下执行  .venv/bin/python seed_demo.py
幂等：每次运行先清空业务表再插入，可反复重跑。
"""
from datetime import date

from app import db, models
from app.services import records


def D(s: str) -> date | None:
    """'YYYY-MM-DD' -> date；空串/None -> None。"""
    if not s:
        return None
    y, m, dd = s.split("-")
    return date(int(y), int(m), int(dd))


# 每户：户主信息 + 成员（含户主本人）+ 户级标签 + 人级标签
HOUSEHOLDS = [
    {
        "hz_name": "张伟", "hz_idcard": "430111196803150011",
        "phone": "13807311101", "address": "青山村1组18号",
        "members": [
            {"name": "张伟", "idcard": "430111196803150011", "gender": "男", "birth": "1968-03-15",
             "relation": "户主", "education": "初中", "health": "健康", "skill": "务农", "tags": []},
            {"name": "李秀兰", "idcard": "430111197005200022", "gender": "女", "birth": "1970-05-20",
             "relation": "配偶", "education": "小学", "health": "健康", "skill": "务农", "tags": []},
            {"name": "张强", "idcard": "430111199209180033", "gender": "男", "birth": "1992-09-18",
             "relation": "子", "education": "大专", "health": "健康", "skill": "数控",
             "tags": [{"type": "employment", "period": "",
                       "extra": {"workplace": "广东省深圳市宝安区", "employer": "华科电子厂",
                                 "job_type": "数控操作工", "monthly_income": 5500,
                                 "work_start": "2022-03-01", "work_end": ""}}]},
        ],
        "tags": [
            {"type": "poverty_alleviated", "status": "已退出", "start_date": "2019-01-01", "end_date": "2020-12-31",
             "extra": {"poverty_year": "2020", "poverty_reason": "因病", "helper": "李书记",
                       "measures": "健康帮扶、产业帮扶"}},
            {"type": "dibao", "status": "享受中", "start_date": "2021-01-01", "end_date": None,
             "extra": {"member_num": 2, "monthly_amount": 820, "dibao_category": "农村低保"}},
            {"type": "subsidy", "status": "享受中", "start_date": "2025-01-01", "end_date": None,
             "extra": {"subsidy_type": "耕地地力保护补贴", "subsidy_year": "2025",
                       "subsidy_area": 4.2, "subsidy_amount": 462,
                       "pay_status": "已发放", "pay_date": "2025-07-15"}},
        ],
    },
    {
        "hz_name": "王芳", "hz_idcard": "430111197508120041",
        "phone": "13807311102", "address": "青山村2组6号",
        "members": [
            {"name": "王芳", "idcard": "430111197508120041", "gender": "女", "birth": "1975-08-12",
             "relation": "户主", "education": "初中", "health": "健康", "skill": "务农", "tags": []},
            {"name": "王小明", "idcard": "430111200001050052", "gender": "男", "birth": "2000-01-05",
             "relation": "子", "education": "初中", "health": "残疾", "skill": "",
             "tags": [{"type": "disabled", "period": "",
                       "extra": {"disability_no": "43011120000105005242", "disability_category": "肢体",
                                 "disability_level": "三级", "cert_date": "2018-06-12"}}]},
        ],
        "tags": [
            {"type": "dibao", "status": "享受中", "start_date": "2022-01-01", "end_date": None,
             "extra": {"member_num": 2, "monthly_amount": 640, "dibao_category": "农村低保"}},
        ],
    },
    {
        "hz_name": "刘建国", "hz_idcard": "430111195506150063",
        "phone": "13807311103", "address": "青山村3组2号",
        "members": [
            {"name": "刘建国", "idcard": "430111195506150063", "gender": "男", "birth": "1955-06-15",
             "relation": "户主", "education": "小学", "health": "残疾", "skill": "",
             "tags": [{"type": "disabled", "period": "",
                       "extra": {"disability_no": "43011119550615006311", "disability_category": "视力",
                                 "disability_level": "一级", "cert_date": "2015-03-08"}},
                      {"type": "med_aid", "period": "",
                       "extra": {"disease": "白内障", "treat_date": "2025-11-10",
                                 "total_cost": 8600, "insure_reimburse": 5200,
                                 "major_aid": 1800, "self_pay": 1600}}]},
        ],
        "tags": [
            {"type": "tekun", "status": "享受中", "start_date": "2020-05-01", "end_date": None,
             "extra": {"support_mode": "分散供养", "monthly_amount": 980, "care_level": "二档"}},
        ],
    },
    {
        "hz_name": "陈志强", "hz_idcard": "430111198003200071",
        "phone": "13807311104", "address": "青山村4组10号",
        "members": [
            {"name": "陈志强", "idcard": "430111198003200071", "gender": "男", "birth": "1980-03-20",
             "relation": "户主", "education": "高中", "health": "健康", "skill": "驾驶",
             "tags": [
                 {"type": "party", "period": "",
                  "extra": {"join_date": "2021-07-01", "party_post": "村党支部书记",
                            "org_location": "青山村党支部"}},
                 {"type": "employment", "period": "",
                  "extra": {"workplace": "湖南省长沙市望城区", "employer": "本地合作社",
                            "job_type": "货运司机", "monthly_income": 4800,
                            "work_start": "2021-02-01", "work_end": ""}},
             ]},
            {"name": "赵丽", "idcard": "430111198207010082", "gender": "女", "birth": "1982-07-01",
             "relation": "配偶", "education": "初中", "health": "健康", "skill": "务农", "tags": []},
            {"name": "陈晨", "idcard": "430111200811230093", "gender": "男", "birth": "2008-11-23",
             "relation": "子", "education": "高中在读", "health": "健康", "skill": "",
             "tags": [{"type": "edu_aid", "period": "2026",
                       "extra": {"edu_stage": "高中", "school": "望城一中", "aid_type": "助学金",
                                 "aid_amount": 1000, "semester": "春季", "period": "2026"}}]},
        ],
        "tags": [
            {"type": "monitoring", "status": "享受中", "start_date": "2024-06-01", "end_date": None,
             "extra": {"monitor_category": "脱贫不稳定户", "risk_type": "因病风险",
                       "risk_end_date": ""}},
        ],
    },
    {
        "hz_name": "杨桂英", "hz_idcard": "430111196210140101",
        "phone": "13807311105", "address": "青山村5组1号",
        "members": [
            {"name": "杨桂英", "idcard": "430111196210140101", "gender": "女", "birth": "1962-10-14",
             "relation": "户主", "education": "小学", "health": "健康", "skill": "务农",
             "tags": [{"type": "med_aid", "period": "",
                       "extra": {"disease": "高血压住院", "treat_date": "2025-09-05",
                                 "total_cost": 4600, "insure_reimburse": 3100,
                                 "major_aid": 900, "self_pay": 600}}]},
        ],
        "tags": [
            {"type": "poverty_alleviated", "status": "已退出", "start_date": "2018-01-01", "end_date": "2019-12-31",
             "extra": {"poverty_year": "2019", "poverty_reason": "缺劳动力", "helper": "王主任",
                       "measures": "兜底保障、公益岗"}},
        ],
    },
    {
        "hz_name": "周军", "hz_idcard": "430111197806090112",
        "phone": "13807311106", "address": "青山村6组8号",
        "members": [
            {"name": "周军", "idcard": "430111197806090112", "gender": "男", "birth": "1978-06-09",
             "relation": "户主", "education": "高中", "health": "健康", "skill": "水电安装",
             "tags": [{"type": "veteran", "period": "",
                       "extra": {"enlist_date": "1998-12-01", "retire_date": "2018-12-01",
                                 "preferential_category": "两参人员", "honor_plaque": "是"}}]},
            {"name": "周婷", "idcard": "430111201003120123", "gender": "女", "birth": "2010-03-12",
             "relation": "女", "education": "初中在读", "health": "健康", "skill": "",
             "tags": [{"type": "edu_aid", "period": "2026",
                       "extra": {"edu_stage": "义务教育", "school": "青山中学", "aid_type": "寄宿生补助",
                                 "aid_amount": 625, "semester": "春季", "period": "2026"}}]},
        ],
        "tags": [],
    },
    {
        "hz_name": "吴建国", "hz_idcard": "430111196511080134",
        "phone": "13807311107", "address": "青山村7组3号",
        "members": [
            {"name": "吴建国", "idcard": "430111196511080134", "gender": "男", "birth": "1965-11-08",
             "relation": "户主", "education": "初中", "health": "健康", "skill": "木工",
             "tags": [{"type": "employment", "period": "",
                       "extra": {"workplace": "湖南省长沙市雨花区", "employer": "宏达装修公司",
                                 "job_type": "木工", "monthly_income": 6000,
                                 "work_start": "2020-05-01", "work_end": ""}}]},
            {"name": "孙梅", "idcard": "430111196703250145", "gender": "女", "birth": "1967-03-25",
             "relation": "配偶", "education": "初中", "health": "健康", "skill": "务农",
             "tags": [
                 {"type": "medical", "period": "2026",
                  "extra": {"period": "2026", "insured": "已参保", "payment_level": "一档",
                            "payment_amount": 380, "payment_date": "2025-12-20"}},
                 {"type": "pension", "period": "2026",
                  "extra": {"period": "2026", "payment_level": "二档", "payment_amount": 500,
                            "receive_status": "领取中", "monthly_pension": 168}},
             ]},
        ],
        "tags": [
            {"type": "subsidy", "status": "享受中", "start_date": "2025-01-01", "end_date": None,
             "extra": {"subsidy_type": "种粮补贴", "subsidy_year": "2025",
                       "subsidy_area": 6.0, "subsidy_amount": 720,
                       "pay_status": "已发放", "pay_date": "2025-07-20"}},
        ],
    },
    {
        "hz_name": "郑秀珍", "hz_idcard": "430111195809170156",
        "phone": "13807311108", "address": "青山村8组5号",
        "members": [
            {"name": "郑秀珍", "idcard": "430111195809170156", "gender": "女", "birth": "1958-09-17",
             "relation": "户主", "education": "小学", "health": "健康", "skill": "",
             "tags": [
                 {"type": "medical", "period": "2026",
                  "extra": {"period": "2026", "insured": "已参保", "payment_level": "一档",
                            "payment_amount": 380, "payment_date": "2025-12-18"}},
                 {"type": "pension", "period": "2026",
                  "extra": {"period": "2026", "payment_level": "二档", "payment_amount": 500,
                            "receive_status": "领取中", "monthly_pension": 175}},
             ]},
        ],
        "tags": [],
    },
]

PROJECTS = [
    {"name": "青山村通组道路硬化工程", "category": "基础设施", "content": "硬化村内4条通组道路，总长3.2公里",
     "invest_amount": 1200000, "fund_source": "财政衔接资金", "start_date": "2025-03-01",
     "end_date": "2026-06-30", "progress": "80%"},
    {"name": "村集体茶叶种植基地", "category": "产业项目", "content": "流转荒山200亩发展有机茶种植",
     "invest_amount": 500000, "fund_source": "村集体+帮扶资金", "start_date": "2025-10-01",
     "end_date": "2027-12-31", "progress": "60%"},
    {"name": "党群服务中心改造", "category": "公共服务", "content": "改造党群服务中心，增设便民服务大厅",
     "invest_amount": 350000, "fund_source": "财政补助", "start_date": "2025-01-01",
     "end_date": "2025-12-31", "progress": "100%"},
]


def clear(s):
    for m in (models.PersonTag, models.HouseholdTag, models.Person, models.Household, models.Project):
        s.query(m).delete()
    s.commit()


def seed():
    db.init_db()
    s = db.SessionLocal()
    clear(s)
    n_house = n_person = n_htag = n_ptag = 0
    try:
        for hh in HOUSEHOLDS:
            member_count = len(hh["members"])
            h = records.find_or_create_household(s, {
                "hz_idcard": hh["hz_idcard"], "hz_name": hh["hz_name"],
                "phone": hh["phone"], "address": hh["address"],
                "member_count": member_count,
            })
            n_house += 1
            for m in hh["members"]:
                p = records.find_or_create_person(s, {
                    "name": m["name"], "idcard": m["idcard"], "gender": m["gender"],
                    "birth": D(m["birth"]), "relation": m["relation"],
                    "education": m["education"], "health": m["health"], "skill": m["skill"],
                }, household_id=h.id)
                n_person += 1
                for t in m["tags"]:
                    s.add(models.PersonTag(
                        person_id=p.id, tag_type=t["type"], period=t.get("period", ""),
                        start_date=D(t["extra"].get("start_date") or ""),
                        end_date=D(t["extra"].get("end_date") or ""),
                        extra={k: v for k, v in t["extra"].items() if v != ""},
                        remark=""))
                    n_ptag += 1
            for t in hh["tags"]:
                s.add(models.HouseholdTag(
                    household_id=h.id, tag_type=t["type"], status=t["status"],
                    start_date=D(t["start_date"]), end_date=D(t["end_date"]),
                    extra={k: v for k, v in t["extra"].items() if v != ""},
                    remark=""))
                n_htag += 1
        for pr in PROJECTS:
            s.add(models.Project(
                name=pr["name"], category=pr["category"], content=pr["content"],
                invest_amount=pr["invest_amount"], fund_source=pr["fund_source"],
                start_date=D(pr["start_date"]), end_date=D(pr["end_date"]),
                progress=pr["progress"], remark=""))
        s.commit()
    finally:
        s.close()
    print(f"完成：{n_house} 户 / {n_person} 人 / 户级标签 {n_htag} / 人级标签 {n_ptag} / 项目 {len(PROJECTS)}")


def maybe_seed() -> bool:
    """首次启动（业务库为空）时自动灌入演示数据，返回是否执行了 seed。

    仅当 household 表为空时执行，不覆盖已有真实数据；删除 data 目录后重启即可重新生成演示数据。
    """
    db.init_db()
    s = db.SessionLocal()
    try:
        empty = s.query(models.Household).count() == 0
    finally:
        s.close()
    if empty:
        seed()
        return True
    return False


if __name__ == "__main__":
    seed()
