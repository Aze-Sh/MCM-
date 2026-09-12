"""Offline entry point for Questions 1 and 2."""
import argparse
import json
import math
from pathlib import Path
from geometry import solve_wedges
from strategy import second_point, second_point_region
from q2_design import optimize_angle
from q2_budget import minimum_movement


def main():
    parser = argparse.ArgumentParser(description="前两问的离线几何计算；不连接任何接口")
    parser.add_argument("input", type=Path, help="JSON：observations，或 first 与 bearing_deg")
    parser.add_argument("--problem", type=int, choices=(1,2), required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8-sig"))
    if args.problem == 1:
        result = solve_wedges(data["observations"], data.get("epsilon_deg",1.005))
    else:
        design=optimize_angle(data['movement_m']) if 'movement_m' in data else minimum_movement(data.get('target_diameter_m',163.))
        theta=math.radians(data["bearing_deg"]);u=(math.cos(theta),math.sin(theta));v=(-u[1],u[0])
        options=[tuple(data["first"][i]+design["a_m"]*u[i]+sign*design["b_m"]*v[i] for i in (0,1)) for sign in (1,-1)]
        p=min(options,key=lambda p:math.dist(p,data["current"])) if "current" in data else options[0]
        result = dict(second_position=dict(x=p[0],y=p[1]),
                      candidate_region=second_point_region(tuple(data["first"]),data["bearing_deg"],data.get("query")),
                      guaranteed_diameter_bound_m=design["diameter_upper_m"],
                      optimization=design,
                      selection_status=("Minimum movement for the requested analytic diameter bound; certified remaining radius gap is reported" if 'movement_m' not in data else "Analytic diameter bound optimized over the full feasible angle interval at the chosen movement radius"),
                      rule="movement_m is measured from first; nearest symmetric side if current supplied",
                      scope="全向信号；首次方向有效；半径1000至1500米")
    rendered = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)
    if args.output:
        args.output.write_text(rendered+"\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
