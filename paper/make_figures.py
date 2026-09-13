from pathlib import Path
import json
import math
import sys
import os
os.environ.setdefault('MPLCONFIGDIR', '/tmp/mcm-paper-matplotlib')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Circle, Polygon, FancyBboxPatch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from jammer_solver import solver as v8, exact_geometry as g
from jammer_solver.questions import optimize_angle, solve_wedges
PAPER=ROOT/'paper'
DATA=json.loads((PAPER/'results.json').read_text())
font_candidates = [
    os.environ.get('MCM_PAPER_FONT'),
    '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',
    'C:/Windows/Fonts/simhei.ttf',
    '/System/Library/Fonts/PingFang.ttc',
]
font_family = None
for candidate in font_candidates:
    if candidate and Path(candidate).is_file():
        font_manager.fontManager.addfont(candidate)
        font_family = font_manager.FontProperties(fname=candidate).get_name()
        break
if font_family is None:
    raise SystemExit('Set MCM_PAPER_FONT to an installed Chinese TrueType font before regenerating figures.')
plt.rcParams.update({'font.family':[font_family,'DejaVu Sans'],'mathtext.fontset':'dejavuserif','font.size':10,'axes.labelsize':10,'legend.fontsize':9,'axes.titlesize':11,'axes.unicode_minus':False,'lines.linewidth':2,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':320,'pdf.fonttype':42})
BLUE='#0072B2';RED='#D55E00';GREEN='#009E73';PURPLE='#7B61A8';GRAY='#555555'

def save(fig,name):
    fig.savefig(PAPER/'figures'/f'{name}.pdf',bbox_inches='tight',pad_inches=.04)
    fig.savefig(PAPER/'figures'/f'{name}.png',bbox_inches='tight',pad_inches=.04,dpi=180)
    plt.close(fig)

def equal(ax,xlabel='东向坐标 / m',ylabel='北向坐标 / m'):
    ax.set_aspect('equal');ax.set_xlabel(xlabel);ax.set_ylabel(ylabel);ax.grid(alpha=.18)

fig,ax=plt.subplots(figsize=(6.3,3.2));ax.set_xlim(0,10);ax.set_ylim(0,5);ax.axis('off')
boxes=[(0.1,3.2,2.65,1.0,'实际观测\n方向 / 近距 / 阴性',BLUE),(3.6,3.2,2.65,1.0,'证据账本\n频道状态与可行域',BLUE),(7.1,3.2,2.65,1.0,'完成证书\n实际清除 + 排除未知',GREEN),(0.1,.55,2.65,1.15,'覆盖搜索\nQ3：7站 / Q4：21站',GRAY),(3.6,.55,2.65,1.15,'联合任务排序\n移动 + 测向 + 清除',BLUE),(7.1,.55,2.65,1.15,'执行下一动作\n射频 / 完整光学链',RED)]
for x,y,w,h,t,c in boxes:
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.06',linewidth=1.5,edgecolor=c,facecolor='white'));ax.text(x+w/2,y+h/2,t,ha='center',va='center',fontsize=10)
for a,b in [((2.8,3.7),(3.5,3.7)),((6.3,3.7),(7,3.7)),((2.8,1.1),(3.5,1.1)),((6.3,1.1),(7,1.1)),((4.9,3.1),(4.9,1.8)),((8.5,1.8),(8.5,2.4)),((8.5,2.4),(1.4,2.4)),((1.4,2.4),(1.4,3.1))]:
 ax.annotate('',b,a,arrowprops=dict(arrowstyle='->',lw=1.5,color=GRAY))
ax.text(5,4.65,'评分决定“先做什么”；证书决定“能否完成”',ha='center',fontsize=11)
save(fig,'flow')

fig,axs=plt.subplots(1,2,figsize=(6.3,2.8),layout='constrained')
obs=[dict(x=0,y=0,bearing_deg=45),dict(x=100,y=0,bearing_deg=135)]
region=solve_wedges(obs);poly=np.array(region['vertices'])
ax=axs[0];ax.add_patch(Polygon(poly,facecolor='#DCECF5',edgecolor=BLUE,lw=2));a,b=np.array(region['farthest_pair']);ax.plot([a[0],b[0]],[a[1],b[1]],'o--',color=RED,ms=4)
ax.set_xlim(47.5,52.5);ax.set_ylim(47.5,52.5);equal(ax);ax.set_title('(a) 两次观测的交会区域')
ax.text(50,47.8,'D = 3.5096 m',ha='center',fontsize=9)
ax=axs[1];tri=np.array([[-.5,0],[.5,0],[0,np.sqrt(3)/2]])
ax.add_patch(Polygon(tri,fill=False,edgecolor='black',lw=2));ax.add_patch(Circle((0,0),.5,fill=False,ls='--',color=RED,lw=2));ax.add_patch(Circle((0,np.sqrt(3)/6),1/np.sqrt(3),fill=False,ls='-.',color=BLUE,lw=2));ax.scatter(*tri.T,color='black',s=20)
ax.set_xlim(-.8,.8);ax.set_ylim(-.65,1);equal(ax,'x / d','y / d');ax.set_title('(b) 同直径圆的反例')
ax.plot([],[],'--',color=RED,label='半径 d/2');ax.plot([],[],'-.',color=BLUE,label=r'半径 $d/\sqrt{3}$');ax.legend(loc='lower center',fontsize=8)
save(fig,'q1_geometry')

fig,axs=plt.subplots(1,2,figsize=(6.3,2.85),layout='constrained')
a=np.linspace(0,1100,500);b=np.linspace(-1100,1100,600);A,B=np.meshgrid(a,b);eps=math.radians(1.005)
mask=(A*A+B*B<=1000**2)
for s in [-1,1]:mask&=((A-1000*math.cos(eps))**2+(B-s*1000*math.sin(eps))**2<=1000**2)
axs[0].contourf(A,B,mask.astype(float),levels=[.5,1.5],colors=['#DCECF5']);axs[0].contour(A,B,mask.astype(float),levels=[.5],colors=[BLUE],linewidths=1.5)
p=DATA['q2_minimum'];axs[0].plot(p['a_m'],p['b_m'],'*',ms=10,color=RED);axs[0].plot(500,840,'s',ms=4,color=GREEN)
axs[0].set_title('(a) 保证接收的候选区域');equal(axs[0],'前向位移 a / m','侧向位移 b / m')
rs=np.linspace(500,999,50);vals=[optimize_angle(float(r))['diameter_upper_m'] for r in rs]
axs[1].plot(rs,vals,color=BLUE);axs[1].axhline(163,ls='--',color=RED,lw=1.5);axs[1].plot(p['movement_m'],p['diameter_upper_m'],'o',color=RED)
axs[1].set_xlabel('移动预算 ρ / m');axs[1].set_ylabel('解析直径上界 / m');axs[1].set_title('(b) 移动与定位精度的折中');axs[1].grid(alpha=.18)
save(fig,'q2_design')

fig,axs=plt.subplots(1,2,figsize=(6.3,3.1),layout='constrained')
for ax,problem in zip(axs,[3,4]):
 q=np.array(v8.search_points(problem));ax.add_patch(Circle((0,0),1800,fill=False,color='black',lw=1.6))
 if problem==3:
  for p in q:ax.add_patch(Circle(p,1000,fill=False,color=BLUE,lw=.65,alpha=.45))
 else:
  ax.plot(*q[1:9].T,'o',color=BLUE,ms=4);ax.plot(*q[9:].T,'s',color=RED,ms=4)
 ax.plot(q[:,0],q[:,1],'o',color=BLUE,ms=3.5);ax.plot(0,0,'*',color='black',ms=9)
 ax.set_xlim(-2400,2400);ax.set_ylim(-2400,2400);equal(ax);ax.set_xticks([-1800,0,1800]);ax.set_yticks([-1800,0,1800]);ax.set_title(f'问题{problem}：{len(q)}个搜索站')
save(fig,'coverage_layouts')

fig,axs=plt.subplots(1,2,figsize=(6.3,2.95),layout='constrained')
ax=axs[0];source=np.array([0.,0.]);witness=np.array([[-450,-300],[500,-200],[150,550]])
ax.add_patch(Polygon(witness,facecolor='#DCECF5',edgecolor=BLUE,lw=2));ax.scatter(*witness.T,color=BLUE,s=35);ax.plot(0,0,'*',ms=12,color=RED)
ax.fill_between([-650,700],-600,600,color=GREEN,alpha=.05);ax.axvline(0,color=GRAY,ls='--',lw=1.5);ax.annotate('任意闭半平面\n至少包含一个证据点',(20,10),(70,-530),arrowprops=dict(arrowstyle='->',lw=1.3),fontsize=9)
ax.set_xlim(-650,700);ax.set_ylim(-650,750);equal(ax);ax.set_title('(a) 源位于近邻测点凸包内')
ax=axs[1];o=(0,0);a=(750,-200);b=(750,200)
ax.add_patch(Polygon([a,(1250,-1000/3),(1250,1000/3),b],facecolor='#F5DFD4',edgecolor=RED,lw=2));ax.plot([0,1300],[0,0],':',color=GRAY);ax.plot(0,0,'*',ms=11,color=GREEN);ax.plot([750,750],[-200,200],'s',color=RED);ax.text(60,60,'实际阳性锚点',fontsize=9);ax.text(1020,-80,'可排除部分',ha='center',fontsize=9);ax.text(780,360,'双阴性测点',fontsize=9)
ax.set_xlim(-100,1350);ax.set_ylim(-500,500);equal(ax);ax.set_title('(b) 双阴性收缩的几何条件')
save(fig,'directional_proof')

from fractions import Fraction
snapshot=json.loads((PAPER/'figure-data.json').read_text())
chain=snapshot['event']
poly=tuple(tuple(Fraction(x) for x in p) for p in snapshot['polygon_rational'])
points=[g.point(p) for p in chain['points']]
origin=np.array(g.floating(points[0]))
axis=np.array(g.floating(points[-1]))-origin
axis/=np.linalg.norm(axis)
normal=np.array([-axis[1],axis[0]])
def local(point):
    delta=np.array(g.floating(point))-origin
    return np.array([delta@axis,delta@normal])
fig,ax=plt.subplots(figsize=(6.3,2.35),layout='constrained');colors=[BLUE,RED,GREEN,PURPLE]
for i,q in enumerate(points):
 part=poly
 for other in points:
  if q!=other:part=g.clip(part,g.sub(other,q),(g.dot(other,other)-g.dot(q,q))/2)
 color=colors[i%len(colors)];qf=local(q)
 ax.add_patch(Circle(qf,19.8,fill=False,ls='--',color=color,lw=1.6))
 if part:ax.add_patch(Polygon([local(v) for v in part],facecolor=color,edgecolor=color,alpha=.23))
 ax.plot(*qf,'o',color=color,ms=4);ax.annotate(str(i+1),qf,xytext=(5,4),textcoords='offset points',fontsize=9)
qs=np.array([local(q) for q in points]);ax.plot(qs[:,0],qs[:,1],'-',color=GRAY,lw=1.2)
ax.add_patch(Polygon([local(v) for v in poly],fill=False,color='black',lw=2));ax.autoscale_view()
equal(ax,'沿链轴坐标 / m','横向坐标 / m')
ax.set_title('实际决策时的完整可行域与光学覆盖链')
save(fig,'optical_chain')

fig,axs=plt.subplots(1,2,figsize=(6.3,2.85),layout='constrained')
for p,c,m in [(3,BLUE,'o'),(4,RED,'s')]:
 rows=[r for r in DATA['comparison'] if r['problem']==p]
 axs[0].scatter([r['v7_s'] for r in rows],[r['v8_s'] for r in rows],c=c,marker=m,s=28,label=f'问题{p}')
axs[0].plot([2500,8200],[2500,8200],'--',color=GRAY,lw=1.5);axs[0].set_xlim(2500,8200);axs[0].set_ylim(2500,8200);axs[0].set_xlabel('v7 总虚拟时间 / s');axs[0].set_ylabel('v8 总虚拟时间 / s');axs[0].legend();axs[0].grid(alpha=.18)
for j,p in enumerate([3,4]):
 rows=[r for r in DATA['cases'] if r['name'].startswith(f'q{p}-') and r['suite'] in ('matched','validation','fresh')]
 costs=[np.mean([r['moving_distance_m']/5 for r in rows]),np.mean([r['counts']['measure']*5 for r in rows]),np.mean([r['counts']['switch'] for r in rows]),np.mean([r['counts']['successful_clear']*5+(r['counts']['clear']-r['counts']['successful_clear'])*3 for r in rows])]
 base=0
 for i,(value,color,label) in enumerate(zip(costs,[BLUE,RED,GREEN,PURPLE],['移动','测向','切频','光学与清除'])):
  axs[1].bar(j,value,bottom=base,width=.58,color=color,label=label if j==0 else None,hatch=['','//','xx','..'][i]);base+=value
axs[1].set_xticks([0,1],['问题3','问题4']);axs[1].set_ylabel('平均虚拟时间 / s');axs[1].legend(fontsize=8,ncol=2,loc='upper left');axs[1].set_ylim(0,8200)
save(fig,'performance')

fig,axs=plt.subplots(1,2,figsize=(6.3,2.7),layout='constrained')
for i,c in enumerate(DATA['calibration']):
 axs[0].plot([v['depth'] for v in c['rollout']],[v['gap_s'] for v in c['rollout']],['o-','s--','^-.'][i],color=[BLUE,RED,GREEN][i],label=f'有限问题 {i+1}')
axs[0].set_xlabel('前瞻深度');axs[0].set_ylabel('距有限问题最优值 / s');axs[0].set_xticks(range(4));axs[0].grid(alpha=.18);axs[0].legend(fontsize=8)
ns=list(range(10,17))
for p,c,m in [(3,BLUE,'o-'),(4,RED,'s--')]:
 vals=[0 if n==16 else (20-n)*DATA['absence_cost'][str(p)] for n in ns];axs[1].plot(ns,vals,m,color=c,label=f'问题{p}')
axs[1].set_xlabel('实际源总数 N');axs[1].set_ylabel('无源频道的必要操作成本 / s');axs[1].set_xticks(ns);axs[1].grid(alpha=.18);axs[1].legend(fontsize=8)
save(fig,'calibration_bounds')

fig,axs=plt.subplots(1,2,figsize=(6.3,2.65),layout='constrained')
for ax,p in zip(axs,[3,4]):
 rows=[r for r in DATA['practice'] if r['problem']==p]
 x=[r['reported_source_count'] if p==3 else r['reported_directional'] for r in rows]
 y=[r['reported_virtual_time_s'] for r in rows]
 ax.scatter(x,y,color=BLUE if p==3 else RED,s=32)
 for i,(xx,yy) in enumerate(zip(x,y)):ax.annotate(str(i+1),(xx,yy),xytext=(5,4),textcoords='offset points',fontsize=9)
 ax.set_xlabel('截图报告源个数' if p==3 else '截图报告定向源个数');ax.set_ylabel('截图报告总时间 / s');ax.set_title(f'问题{p}：五次不同案例');ax.grid(alpha=.18)
save(fig,'practice')
print('Generated 9 figures in PDF and PNG formats')
