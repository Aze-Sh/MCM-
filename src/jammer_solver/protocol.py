import json
import math
import os
import time
import uuid
from urllib.request import Request as qqcls, ProxyHandler as dlcls, build_opener as ljq


def jyhf(path, reply):
    if not isinstance(reply, dict) or type(reply.get("accepted")) is not bool:
        raise RuntimeError("Malformed acceptance status")
    if not reply["accepted"]:
        raise RuntimeError("accepted=false: action did not execute")
    if (
        not (
            type(reply.get("virtual_time_s")) in (int, float)
            and math.isfinite(reply.get("virtual_time_s"))
        )
        or reply["virtual_time_s"] < 0
    ):
        raise RuntimeError("Malformed virtual time in accepted response")
    if path == "/enter":
        seconds = reply.get("remaining_real_duration_s")
        if (
            not (type(seconds) in (int, float) and math.isfinite(seconds))
            or not 0 <= seconds <= 1200
            or int(seconds) != seconds
        ):
            raise RuntimeError("Malformed remaining real duration")
        if (
            not (
                type(reply.get("max_virtual_duration_s")) in (int, float)
                and math.isfinite(reply.get("max_virtual_duration_s"))
            )
            or reply["max_virtual_duration_s"] <= 0
        ):
            raise RuntimeError("Malformed maximum virtual duration")
    elif path == "/measure":
        result = reply.get("measure_result")
        if result not in ("direction", "near", "no_signal"):
            raise RuntimeError("Unknown measure result")
        if result == "direction":
            angle = reply.get("svd_deg")
            if (
                not (type(angle) in (int, float) and math.isfinite(angle))
                or not 0 <= angle < 360
            ):
                raise RuntimeError("Malformed bearing")
    elif path == "/clear" and reply.get("clear_result") not in (
        "success",
        "no_target_in_range",
    ):
        raise RuntimeError("Unknown clear result")
    elif path == "/exit" and reply.get("exit_reason") != "user_exit":
        raise RuntimeError("Unknown exit result")


def xjjk(dh, rizhi, url="http://127.0.0.1:2026"):
    jiekou = dict(pending=None, deadline=math.inf)
    bianhao = uuid.uuid4().hex[:16]
    xulie = 0
    opener = ljq(dlcls({}))

    def baocun(shijian):
        rizhi.write(json.dumps(shijian, ensure_ascii=False, allow_nan=False) + "\n")
        rizhi.flush()
        os.fsync(rizhi.fileno())

    def qingqiu(path, weizhi=None, pindao=None):
        nonlocal xulie
        if jiekou["pending"] is not None:
            raise RuntimeError("Previous request has no confirmed response")
        shengyu = jiekou["deadline"] - time.monotonic()
        if shengyu <= 0:
            raise TimeoutError("Request deadline reached")
        xulie += 1
        neirong = dict(arena_id="default", robot_id=dh, request_id=f"{bianhao}-{xulie}")
        if path in ("/measure", "/clear"):
            neirong.update(position=dict(x=weizhi[0], y=weizhi[1]), channel=pindao)
        zhengwen = json.dumps(
            neirong, ensure_ascii=False, allow_nan=False, separators=(",", ":")
        ).encode("utf-8")
        baocun(dict(event="intent", wall_time=time.time(), path=path, payload=neirong))
        jiekou["pending"] = dict(path=path, payload=neirong)
        request = qqcls(
            url + path,
            data=zhengwen,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with opener.open(request, timeout=min(5.0, shengyu)) as response:
            huifu = json.loads(response.read().decode("utf-8"))
            baocun(
                dict(
                    event="response",
                    wall_time=time.time(),
                    request_id=neirong["request_id"],
                    attempt=0,
                    http_status=response.status,
                    response=huifu,
                )
            )
            if response.status != 200:
                raise RuntimeError(f"HTTP {response.status}")
        jyhf(path, huifu)
        jiekou["pending"] = None
        return huifu

    jiekou.update(call=qingqiu, record=baocun)
    return jiekou
