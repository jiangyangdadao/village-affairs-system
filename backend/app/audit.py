import json
from datetime import datetime

from app import db
from app.models import OperationLog


def write(s, op_type: str, module: str, biz_type: str = "", biz_id: int = 0,
          before: dict | None = None, after: dict | None = None, ip: str = "", note: str = ""):
    s.add(OperationLog(
        op_time=datetime.now(), op_type=op_type, module=module,
        biz_type=biz_type, biz_id=biz_id,
        before_json=json.dumps(before, ensure_ascii=False, default=str) if before is not None else "",
        after_json=json.dumps(after, ensure_ascii=False, default=str) if after is not None else "",
        ip=ip, note=note,
    ))
