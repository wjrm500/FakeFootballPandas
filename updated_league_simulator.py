### bringing in packages and data

import pandas as pd
import numpy as np
import itertools as it
import random as rand
teams = pd.read_excel("team_list.xlsx")
league_ratings = pd.read_excel("league_ratings.xlsx")

### setup

nation = "England"
year = 1900
league_rating = league_ratings.loc[league_ratings["Team"] == nation,
                                   year]
divisions, division = [], 1
for x in range(0, 4):
    for y in range(0, 20):
        divisions.append(division)
    division += 1
divisions = pd.Series(divisions)
temporary_rank = []
for x in range(1, 21):
    temporary_rank.append(x)
temporary_rank = pd.Series(temporary_rank)
temporary_rank = temporary_rank.append([temporary_rank,
                                        temporary_rank,
                                        temporary_rank])
temporary_rank.reset_index(drop = True, 
                       inplace = True)
teams = pd.concat([divisions.rename("division"),
                   temporary_rank.rename("temporary_rank"),
                   teams],
                  axis = 1)

### initialising ratings for teams

ratings = []
for index, row in teams[["division",
                         "temporary_rank"]].iterrows():
    x = league_rating - (row["division"] - 1) * 10
    rating = float(x + 5 - 10 / 19 * (row["temporary_rank"] - 1))
    ratings.append(rating)
teams.drop(["temporary_rank"], axis = 1, inplace = True)
ratings_cache = ratings

### swapping ratings to mimic promotion and relegation

relegation_indices = list(it.chain(range(16, 20),
                                   range(36, 40),
                                   range(56, 60)))
promotion_indices = list(it.chain(range(20, 24),
                                  range(40, 44),
                                  range(60, 64)))
ratings = pd.Series(ratings_cache)
temporary_ratings = []
for index, value in enumerate(ratings):
    if index in relegation_indices:
        temporary_ratings.append(ratings[index + 4])
    elif index in promotion_indices:
        temporary_ratings.append(ratings[index - 4])
    else:
        temporary_ratings.append(ratings[index])
internal_rank_1 = ratings[0:20].rank(ascending = False)
internal_rank_2 = ratings[20:40].rank(ascending = False)
internal_rank_3 = ratings[40:60].rank(ascending = False)
internal_rank_4 = ratings[60:80].rank(ascending = False)
internal_rank = pd.concat([internal_rank_1,
                           internal_rank_2,
                           internal_rank_3,
                           internal_rank_4])
teams = pd.concat([teams,
                   internal_rank.rename("internal_rank")],
                  axis = 1)

### base modifier

base_modifier = []
for index, value in enumerate(ratings):
    if index in relegation_indices:
        mu, sigma = 5, 2
    elif index in promotion_indices:
        mu, sigma = -5, 2
    else:
        mu, sigma = 0, 2
    base_modifier.append(np.random.normal(mu, sigma, 1).item(0))
ratings = ratings + base_modifier

### normaliser

expected_ratings = []
for index, row in teams[["division", "internal_rank"]].iterrows():
    x = league_rating - (row["division"] - 1) * 10
    expected_rating = float(x + 5 - 10 / 19 * (row["internal_rank"] - 1))
    expected_ratings.append(expected_rating)
ratings = (ratings * 3 + expected_ratings) / 4
teams.drop(["internal_rank"], axis = 1, inplace = True)

### attack and defence ratings

mu, sigma = 0, 0.75
random_numbers_ad = pd.Series(np.random.normal(mu, sigma, 80))
mu, sigma = 1.25, 0.0625
random_numbers_ha = pd.Series(np.random.normal(mu, sigma, 80))
attack_ratings = ratings + random_numbers_ad
defence_ratings = ratings - random_numbers_ad

### home / away differential

mu, sigma = 1.25, 0.0625
ha_differential = pd.Series(np.random.normal(mu, sigma, 80))

### randomising fixture slots

slots = []
for i in range(4):
    slot = list(range(1, 21))
    rand.shuffle(slot)
    slots.append(slot)
flat_slots = [item for sublist in slots for item in sublist]
slots = pd.Series(flat_slots)

### core data prep

teams = pd.concat([teams,
                   ratings.rename("ovrRat"),
                   attack_ratings.rename("attRat"),
                   defence_ratings.rename("defRat"),
                   ha_differential.rename("haDiff"),
                   slots.rename("slot")],
                  axis = 1)
teams["form"] = 0

teams_cache = teams

### bringing in external stuff for score calculation

score_table = pd.read_excel("score_table.xlsx")
schedule = pd.read_excel("schedule.xlsx")

schedule.drop("Fixture", inplace = True, axis = 1)
schedule.rename(columns = {"Week": "gameweek",
                           "Home": "home_slot",
                           "Away": "away_slot"},
                inplace = True)

### setup

schedules = []
for i in range (1, 39):
    x = schedule[schedule["gameweek"] == i]
    schedules.append(x)

single_divisions = []
for i in range (1, 5):
    x = teams[teams["division"] == i]
    single_divisions.append(x)
    
results = []
results_1, results_2, results_3, results_4 = [], [], [], []
for i in [results_1,
          results_2,
          results_3,
          results_4]:
    results.append(i)
    
### calculating gameweek-specific overall, attack and defence ratings

for i in range (0, 4):
    for j in range (0, 38):
        print(i, j)
        df = schedules[j].merge(single_divisions[i], left_on = "home_slot", right_on = "slot")
        df = df.merge(single_divisions[i], left_on = "away_slot", right_on = "slot")
        df["haDiff_y"] = df["haDiff_y"].apply(lambda x: - x)
        df["nOvrRat_x"] = df["ovrRat_x"] + (df["ovrRat_x"] / 100 * (df["haDiff_x"] + df["form_x"]))
        df["nAttRat_x"] = df["attRat_x"] + (df["attRat_x"] / 100 * (df["haDiff_x"] + df["form_x"]))
        df["nDefRat_x"] = df["defRat_x"] + (df["defRat_x"] / 100 * (df["haDiff_x"] + df["form_x"]))
        df["nOvrRat_y"] = df["ovrRat_y"] + (df["ovrRat_y"] / 100 * (df["haDiff_y"] + df["form_y"]))
        df["nAttRat_y"] = df["attRat_y"] + (df["attRat_y"] / 100 * (df["haDiff_y"] + df["form_y"]))
        df["nDefRat_y"] = df["defRat_y"] + (df["defRat_y"] / 100 * (df["haDiff_y"] + df["form_y"]))
        df["pot_x"] = df["nAttRat_x"] - df["nDefRat_y"] + 50
        df["pot_y"] = df["nAttRat_y"] - df["nDefRat_x"] + 50
        df["pot_x"].where(df["pot_x"] > 100, 100)
        df["pot_y"].where(df["pot_y"] > 100, 100)
        df["pot_x"].where(df["pot_x"] < 0, 0)
        df["pot_y"].where(df["pot_y"] < 0, 0)
        df["pot_x"] = df["pot_x"].apply(np.floor)
        df["pot_y"] = df["pot_y"].apply(np.floor)

        ### calculating goals scored

        temp_list = []
        big_temp_list = []
        home_and_away = []
        for l in [df["pot_x"], df["pot_y"]]:
            for m in l:
                for n in reversed(range(1, 16)):
                    if rand.random() > score_table.loc[score_table["index"] == m, n].to_list()[0]:
                        temp_list.append(n)
                    else:
                        temp_list.append(0)
                big_temp_list.append(temp_list)
                temp_list = []
            goals = []
            for l in big_temp_list:
                goals.append(max(l))
            big_temp_list = []
            home_and_away.append(goals)
        goals_x = pd.Series(home_and_away[0]).rename("goals_x")
        goals_y = pd.Series(home_and_away[1]).rename("goals_y")
        df = pd.concat([df,
                        goals_x,
                        goals_y],
                       axis = 1)

        ### calculating form values for the specific gameweek

        gFormR_x, gFormR_y = [], [] # form attribute based on result
        for index, row in df.iterrows():
            if df["goals_x"][index] > df["goals_y"][index]:
                gFormR_x.append(0.5)
                gFormR_y.append(-0.5)
            elif df["goals_x"][index] < df["goals_y"][index]:
                gFormR_x.append(-0.5)
                gFormR_y.append(0.5)
            else:
                gFormR_x.append(0)
                gFormR_y.append(0)
        gFormRD_x, gFormRD_y = [], [] # form attribute based on overall rating difference
        for index, row in df.iterrows():
            gFormRD_x.append((df["nOvrRat_y"][index] -  df["nOvrRat_x"][index]) / 20)
            gFormRD_y.append((df["nOvrRat_x"][index] -  df["nOvrRat_y"][index]) / 20)
        gFormGD_x, gFormGD_y = [], [] # form attribute based on goal difference
        for index, row in df.iterrows():
            if abs(df["goals_x"][index] - df["goals_y"][index]) == 1:
                gFormGD_x.append(0)
                gFormGD_y.append(0)
            else:
                gFormGD_x.append((df["goals_x"][index] - df["goals_y"][index]) / 20)
                gFormGD_y.append((df["goals_y"][index] - df["goals_x"][index]) / 20)

        gFormR_x = pd.Series(gFormR_x)
        gFormRD_x = pd.Series(gFormRD_x)
        gFormGD_x = pd.Series(gFormGD_x)
        gFormR_y = pd.Series(gFormR_y)
        gFormRD_y = pd.Series(gFormRD_y)
        gFormGD_y = pd.Series(gFormGD_y)
        gForm_x = gFormR_x + gFormRD_x + gFormGD_x - (df["form_x"] / 5)
        gForm_y = gFormR_y + gFormRD_y + gFormGD_y - (df["form_y"] / 5)
        df = pd.concat([df,
                        gForm_x.rename("gForm_x"),
                        gForm_y.rename("gForm_y")],
                       axis = 1)
        
        results[i].append(df)
        
        formUpdate = results[i][j][["team_x", "team_y", "gForm_x", "gForm_y"]]

        single_divisions[i] = single_divisions[i].merge(formUpdate,
                                                        left_on = "team",
                                                        right_on = "team_x", how = "left")
        single_divisions[i] = single_divisions[i].merge(formUpdate,
                                                        left_on = "team",
                                                        right_on = "team_y", how = "left")
        single_divisions[i]["nForm"] = single_divisions[i]["gForm_x_x"].fillna(single_divisions[i]["gForm_y_y"])
        single_divisions[i].drop("form",
                                 inplace = True,
                                 axis = 1)
        single_divisions[i].rename(columns = {"nForm": "form"},
                                   inplace = True)
        single_divisions[i] = single_divisions[i][["division",
                                                   "slot",
                                                   "team",
                                                   "ovrRat",
                                                   "attRat",
                                                   "defRat",
                                                   "haDiff",
                                                   "form"]]
        
### producing league tables

division = []
team = []
winsSums = []
drawsSums = []
lossesSums = []
pointsSums = []
goalsForSums = []
goalsAgainstSums = []

for g in range (0, 4):
    for h in single_divisions[g]["team"]:
        print(g, h)
        goalsFor = []
        goalsAgainst = []
        for i in results[g]:
            if h in i["team_x"].unique():
                goalsFor.append(i.iloc[i["team_x"].unique().tolist().index(h), i.columns.get_loc("goals_x")])
                goalsAgainst.append(i.iloc[i["team_x"].unique().tolist().index(h), i.columns.get_loc("goals_y")])
            else:
                goalsFor.append(i.iloc[i["team_y"].unique().tolist().index(h), i.columns.get_loc("goals_y")])
                goalsAgainst.append(i.iloc[i["team_y"].unique().tolist().index(h), i.columns.get_loc("goals_x")])

        goalsFor, goalsAgainst = pd.Series(goalsFor), pd.Series(goalsAgainst)
        goalsForAgainst = pd.concat([goalsFor.rename("goalsFor"), goalsAgainst.rename("goalsAgainst")], axis = 1)
        wins, draws, losses, points = [], [], [], []
        for index, row in goalsForAgainst.iterrows():
            if row[0] > row[1]:
                wins.append(1)
                draws.append(0)
                losses.append(0)
                points.append(3)
            elif row[0] == row[1]:
                wins.append(0)
                draws.append(1)
                losses.append(0)
                points.append(1)
            else:
                wins.append(0)
                draws.append(0)
                losses.append(1)
                points.append(0)
        wins, draws, losses, points = pd.Series(wins), pd.Series(draws), pd.Series(losses), pd.Series(points)
        winsSum, drawsSum, lossesSum, pointsSum = wins.sum(), draws.sum(), losses.sum(), points.sum()
        goalsForSum, goalsAgainstSum = goalsFor.sum(), goalsAgainst.sum()
        division.append(g + 1)
        team.append(h)
        winsSums.append(winsSum)
        drawsSums.append(drawsSum)
        lossesSums.append(lossesSum)
        pointsSums.append(pointsSum)
        goalsForSums.append(goalsForSum)
        goalsAgainstSums.append(goalsAgainstSum)
        
### making league tables readable

tables = pd.DataFrame(list(zip(division,
                               team,
                               winsSums,
                               drawsSums,
                               lossesSums,
                               goalsForSums,
                               goalsAgainstSums,
                               pointsSums)),
                           columns = ["Division", "Team", "W", "D", "L", "GF", "GA", "Pts"])
tables["GD"] = tables["GF"] - tables["GA"]
tables = tables[["Division", "Team", "W", "D", "L", "GF", "GA", "GD", "Pts"]]
for i in range(4):
    tables_division = tables[tables["Division"] == i]
    tables_division.sort_values(by = ["Pts", "GD", "GF"], ascending = [False, False, False], inplace = True)
    tables_division.reset_index(drop = True, inplace = True)
    print(tables_division)