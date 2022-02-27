
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import seaborn as sns

from cooling import Cooler
from load import load_data
from team import Team


people = load_data()

cooler = Cooler(
    people,
    size_target=5.5,
    tz_penalty=9,
    exp_penalty=500,
    size_penalty=200,
    lead_penalty=200,
    max_temp=20_000,    # not commensurate with the penalty numbers, this is basically how long you want the algo to run
    init_team_size=5,
)

def audit():
    singleton = Team([list(people)[100]])
    random_team = Team(list(people)[44:49])
    print(singleton)
    print(breakdown(singleton))
    print(random_team)
    print(breakdown(random_team))

def breakdown(team):
    s = f"{len(team)}\n"
    d = cooler.local_energy_audit(team)
    for k,v in d.items():
        s += f"{k}: {v:,.2f}\n"
    s += f"total: {sum(d.values()):,.2f}\n"
    return s

def seaborn():
    sns.set_style("darkgrid")
    cooler.cool(record=True)
    df = pd.DataFrame(cooler.telemetry)
    fig, ((ax00, ax01, ax02), (ax10, ax11, ax12)) = plt.subplots(2, 3)
    xmax = len(df)

    sns.lineplot(
        data=df,
        x=range(xmax),
        y="global_energy",
        ax=ax00,
    )

    events = cooler.telemetry["change_accepted"]
    t = cooler.max_temp//100
    compress = [sum(events[t*i:t*(i+1)]) for i in range(len(events)//t)]
    expand = [compress[i//t] for i in range(len(events))]
    sns.lineplot(
        data=df,
        x=range(xmax),
        y=expand,
        ax=ax01,
        color="red",
    )
    ax01.set_ylabel(f"Acceptance per {t}")

    sns.lineplot(
        data=df,
        x=(round(x, 100) for x in range(xmax)),
        y="delta",
        ax=ax10,
        color="green",
    )

    sns.lineplot(
        data=df,
        x=range(xmax),
        y="avg_size",
        ax=ax11,
    #    color="orange",
    )

    sns.lineplot(
        data=df,
        x=range(xmax),
        y="exp_pen",
        ax=ax12,
        color="green",
    )
    sns.lineplot(
        data=df,
        x=range(xmax),
        y="size_pen",
        ax=ax12,
        color="blue",
    )
    sns.lineplot(
        data=df,
        x=range(xmax),
        y="tz_pen",
        ax=ax12,
        color="orange",
    )
    sns.lineplot(
        data=df,
        x=range(xmax),
        y="lead_pen",
        ax=ax12,
        color="red",
    )
    plt.show()

seaborn()
