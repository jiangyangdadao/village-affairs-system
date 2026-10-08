from dataclasses import dataclass, field

from fastapi import HTTPException


@dataclass
class FieldDef:
    key: str
    label: str
    kind: str = "text"          # text / number / date / select
    required: bool = False
    options: list[str] = field(default_factory=list)


@dataclass
class LedgerDef:
    key: str
    name: str
    scope: str                  # household / person
    tag_type: str | None        # None = 居民信息（直接查 person 表）
    unit: str                   # 户 / 人
    fields: list[FieldDef]
    status_options: list[str] | None = None   # 户级台账状态筛选选项；None 用默认「享受中/已退出」
    status_default: str | None = None         # 户级新建默认状态；None 用「享受中」
    multi: bool = False                        # 允许同人/同户多条记录（不去重，如务工、资助流水）


def _f(key, label, kind="text", required=False, options=None):
    return FieldDef(key=key, label=label, kind=kind, required=required, options=options or [])


LEDGER_LIST = [
    LedgerDef(key="resident", name="居民信息", scope="person", tag_type=None, unit="人",
              fields=[]),  # 基础字段即人员表全部列
    LedgerDef(key="poverty_alleviated", name="脱贫户", scope="household", tag_type="poverty_alleviated", unit="户",
              fields=[
                  _f("poverty_year", "脱贫年度"),
                  _f("poverty_reason", "致贫原因", "select", options=["因病", "因残", "因学", "缺劳动力", "缺资金", "其他"]),
                  _f("helper", "帮扶责任人"),
                  _f("measures", "帮扶措施"),
              ]),
    LedgerDef(key="monitoring", name="监测户", scope="household", tag_type="monitoring", unit="户",
              status_options=["风险未消除", "风险已消除"], status_default="风险未消除",
              fields=[
                  _f("monitor_category", "监测类别", "select", required=True,
                     options=["脱贫不稳定户", "边缘易致贫户", "突发严重困难户"]),
                  _f("risk_type", "风险类型"),
                  _f("risk_end_date", "风险消除时间", "date"),
              ]),
    LedgerDef(key="dibao", name="低保户", scope="household", tag_type="dibao", unit="户",
              fields=[
                  _f("member_num", "保障人数", "number", required=True),
                  _f("monthly_amount", "月保障金", "number", required=True),
                  _f("dibao_category", "低保类别", "select", options=["农村低保", "城市低保"]),
              ]),
    LedgerDef(key="tekun", name="特困供养户", scope="household", tag_type="tekun", unit="户",
              fields=[
                  _f("support_mode", "供养方式", "select", required=True, options=["集中供养", "分散供养"]),
                  _f("monthly_amount", "月供养金", "number"),
                  _f("care_level", "护理等级", "select", options=["一档", "二档", "三档", "无"]),
              ]),
    LedgerDef(key="disabled", name="残疾人", scope="person", tag_type="disabled", unit="人",
              fields=[
                  _f("disability_no", "残疾证号", required=True),
                  _f("disability_category", "残疾类别", "select", required=True,
                     options=["视力", "听力", "言语", "肢体", "智力", "精神", "多重"]),
                  _f("disability_level", "残疾等级", "select", required=True,
                     options=["一级", "二级", "三级", "四级"]),
                  _f("cert_date", "发证日期", "date"),
              ]),
    LedgerDef(key="party", name="党员", scope="person", tag_type="party", unit="人",
              fields=[
                  _f("join_date", "入党时间", "date", required=True),
                  _f("party_post", "党内职务"),
                  _f("org_location", "组织关系所在地"),
              ]),
    LedgerDef(key="veteran", name="退役军人", scope="person", tag_type="veteran", unit="人",
              fields=[
                  _f("enlist_date", "入伍时间", "date"),
                  _f("retire_date", "退役时间", "date"),
                  _f("preferential_category", "优抚类别", "select",
                     options=["在乡老复员军人", "带病回乡", "两参人员", "其他优抚", "无"]),
                  _f("honor_plaque", "是否悬挂光荣牌", "select", options=["是", "否"]),
              ]),
    LedgerDef(key="employment", name="务工信息", scope="person", tag_type="employment", unit="人", multi=True,
              fields=[
                  _f("workplace", "工作地点", required=True),
                  _f("employer", "单位"),
                  _f("job_type", "工种"),
                  _f("monthly_income", "月收入", "number"),
                  _f("work_start", "务工开始", "date"),
                  _f("work_end", "务工结束", "date"),
              ]),
    LedgerDef(key="medical", name="城乡医保", scope="person", tag_type="medical", unit="人",
              fields=[
                  _f("period", "年度", required=True),
                  _f("insured", "参保状态", "select", required=True, options=["已参保", "未参保", "代缴"]),
                  _f("payment_level", "缴费档次", "select", options=["一档", "二档"]),
                  _f("payment_amount", "缴费金额", "number"),
                  _f("payment_date", "缴费时间", "date"),
              ]),
    LedgerDef(key="pension", name="养老保险", scope="person", tag_type="pension", unit="人",
              fields=[
                  _f("period", "年度", required=True),
                  _f("payment_level", "缴费档次", "select", options=["一档", "二档", "三档"]),
                  _f("payment_amount", "缴费金额", "number"),
                  _f("receive_status", "领取状态", "select", options=["未领取", "领取中"]),
                  _f("monthly_pension", "月养老金", "number"),
              ]),
    LedgerDef(key="subsidy", name="惠民补贴", scope="household", tag_type="subsidy", unit="户",
              fields=[
                  _f("subsidy_type", "补贴类型", "select", required=True,
                     options=["耕地地力保护补贴", "种粮补贴", "稻谷补贴", "农机购置补贴", "其他"]),
                  _f("subsidy_year", "补贴年度", required=True),
                  _f("subsidy_area", "补贴面积(亩)", "number"),
                  _f("subsidy_amount", "补贴金额(元)", "number", required=True),
                  _f("pay_status", "发放状态", "select", options=["待发放", "已发放", "发放失败"]),
                  _f("pay_date", "发放时间", "date"),
              ]),
    LedgerDef(key="edu_aid", name="教育资助", scope="person", tag_type="edu_aid", unit="人", multi=True,
              fields=[
                  _f("edu_stage", "学段", "select", required=True,
                     options=["学前教育", "义务教育", "高中", "中职", "高职", "本科"]),
                  _f("school", "学校名称"),
                  _f("aid_type", "资助类型", "select", required=True,
                     options=["雨露计划", "助学金", "免学费", "寄宿生补助", "其他"]),
                  _f("aid_amount", "资助金额(元)", "number"),
                  _f("semester", "学期", "select", options=["春季", "秋季"]),
                  _f("period", "年度"),
              ]),
    LedgerDef(key="med_aid", name="医疗救助", scope="person", tag_type="med_aid", unit="人", multi=True,
              fields=[
                  _f("disease", "疾病名称"),
                  _f("treat_date", "就医时间", "date"),
                  _f("total_cost", "医疗总费用(元)", "number", required=True),
                  _f("insure_reimburse", "医保报销(元)", "number"),
                  _f("major_aid", "大病救助(元)", "number"),
                  _f("self_pay", "自付金额(元)", "number"),
              ]),
]

LEDGERS = {d.key: d for d in LEDGER_LIST}


def get_ledger(key: str) -> LedgerDef:
    if key not in LEDGERS:
        raise HTTPException(404, "未知台账类型")
    return LEDGERS[key]
