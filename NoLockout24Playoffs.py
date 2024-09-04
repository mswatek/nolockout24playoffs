from yahoofantasy import Context, League
import streamlit as st
import pandas as pd
import numpy as np
import requests,base64
import plotly.express as px
from datetime import datetime
import seaborn as sns
import gspread
from google.oauth2.service_account import Credentials
#from time import strftime, localtime

st.set_page_config(layout="wide",page_title="No Lockout! - 2024 Playoffs")
st.title(":blue[No More Lockouts in MLB! - 2024 Playoffs]")


##### ESTABLISH THE CONNECTION #####
##### ESTABLISH THE CONNECTION #####
##### ESTABLISH THE CONNECTION #####


def refreshAuthorizationToken(refreshToken:str) -> dict:
    """Uses existing refresh token to get the new access token"""

    headers: dict = {
        'Authorization': f"Basic {AUTH_HEADER}",
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36',
    }

    data: dict = {
        "redirect_uri": 'oob',
        "grant_type": 'refresh_token',
        "refresh_token": refreshToken
    }

    req = requests.post("https://api.login.yahoo.com/oauth2/get_token",headers=headers,data=data,timeout=100)

    if req.status_code == 200: 

        dobj: dict = req.json()

        return dobj
    
    print("Something went wrong when getting refresh token...try getting the initial access token again!")

    return None


# Plug in your ID & SECRET here from yahoo when you create your app. Make sure you have the correct scope set for fantasy API ex: "read" or "read/write"
CLIENT_ID = "dj0yJmk9VEtpWVNNQzd1TVRtJmQ9WVdrOVRUQkpObXRuTjJrbWNHbzlNQS0tJnM9Y29uc3VtZXJzZWNyZXQmc3Y9MCZ4PTcy"
CLIENT_SECRET = "23f4d294641cc580d381c647f8932711f19a50e8"

# Special auth header for yahoo.
AUTH_HEADER = base64.b64encode(bytes(f"{CLIENT_ID}:{CLIENT_SECRET}".encode("utf-8"))).decode("utf-8")

auth = {
    "access_token": "8gfVehyeulCD48_aK7qLhygosdbMyEFW1fsuuBq32QN8MoZKi4GbTUYkQBnKKCseyQ8u8T65VS74GEVxR_bzbLyZ8O1HCtZz8IVuqwXDLBsJsQFjF.72heACadoNck5sjDKrNGpY.VwqFAoKJFHWoRdhF8Nz_B4Wrr.LWV3WFQunULvnS6A39UF_eHq60H4s7DoZUypxkUp7lqfy7osuZalM1kQASkKWNFlsNogWmJlO6aDU6Ujoo9ZhggvEsY90heL3GsLWSAqjONHcSA6W_6vT4BzTPeFA0M3Se5u0PV6O5LQz8DUxxFeGmBoJ7k8LAxFk0KfVc901fBftS4_ZmMwZtwJUyAsCEnqmjWDsapbAy5eIaiz9LAKAUi_m8S6P2xAhHwqcG2NfDHmGY8pdD7j3KkWerQStNVB6iWDPzjXSpQI18XgVL35oB34GV4n6pWY0di_WMF8v1rFhCJOrMu8afTYnuO6zmD7_G_hJllZDbIT.tXCYOx1p2_A8.HHb.cyOw6Q3qpVOl1Xy33mQmfwVfTxGfDwtuQ5z.85Ka1GUur4kok0laQ6y4kF2qsc4PUMFdhn.p531QtGQToqDsX_1ILeBfCk1FiCe1zNoqfQqn6vBlkVEiJdSjQHR4Ba0spbMzVWIZiKA7mc9vddxf0su6Ho4HwzKQU8.BO0fk2jr3CYLx3Tu4baYReKUTTXBV9oqps6Wn1QBbVUXGjaIe.uFZMsw3DllMnka5I9O74tob3XUA2u8S.kNcIoV4UYn.6jkwKkSw577dOTce.QfWXkWc.rnRvKPX3Q1JRglK7SFfuiVFOuy8Xvu6kFrdjT3SSAwClgmXUcacbocp3zQP8vHSyV9oojCMr_bdXzZC9KRQKZwAUbsbzzf._1RdDYepaP_83dyczYnSPqEHeiY",
    "refresh_token": "AMooCWXYBYMcjT_AzcfJWIeedRC4~000~nJZ43mNIt2q7pdxBi3U-",
    "expires_in": 3600,
    "token_type": "bearer",
}


# Anytime the context is used, I would wrap it in a try except block in case it needs to get a new token.
try:

    ctx = Context(persist_key="oauth2",client_id=CLIENT_ID,client_secret=CLIENT_SECRET,refresh_token=auth["refresh_token"])
    league: list = ctx.get_leagues("mlb", 2024)[0]

except Exception:

    # Get refresh token
    auth = refreshAuthorizationToken(auth["refresh_token"])
    ctx = Context(persist_key="oauth2",client_id=CLIENT_ID,client_secret=CLIENT_SECRET,refresh_token=auth["refresh_token"])
    league: list = ctx.get_leagues("mlb", 2024)[0]


##### BRING IN ALL WEEKS #####
##### BRING IN ALL WEEKS #####
##### BRING IN ALL WEEKS #####


@st.cache_data(ttl=3600)
def load_data():
    all_weeks=pd.DataFrame()
    for i in range(20,22):
        week = league.weeks()[i]
        df = pd.DataFrame({'Team':[],'Opponent':[], 'cat':[], 'stat':[]})
        df2 = pd.DataFrame({'Team':[], 'Opponent':[],'cat':[], 'stat':[]})
        for matchup in week.matchups:
            for team1_stat, team2_stat in zip(matchup.team1_stats, matchup.team2_stats):
                df.loc[len(df)] = [matchup.team1.name,matchup.team2.name, team1_stat.display, team1_stat.value]
                df2.loc[len(df2)] = [matchup.team2.name,matchup.team1.name, team2_stat.display, team2_stat.value]

        df_combined = pd.concat([df,df2])
        df_wide = pd.pivot(df_combined, index=['Team','Opponent'], columns='cat', values='stat')
        df_wide['Week'] = i+1
        frames= [all_weeks,df_wide]
        all_weeks = pd.concat(frames)

    return all_weeks

all_weeks = load_data()

all_weeks=all_weeks.reset_index()


##### Create Matchup Variable #####
##### Create Matchup Variable #####
##### Create Matchup Variable #####

team_list = all_weeks['Team'].tolist()
team_list = list(set(team_list))
id_list = [1,2,4,8,16,32,64,128,256,512,1024,2048] ##creating unique IDs that are unique no matter the combination of adding two together

teams_df = pd.DataFrame(list(zip(team_list, id_list)), columns = ['Name', 'roster_id'])

all_weeks = pd.merge(all_weeks, teams_df, left_on='Team', right_on='Name',how='left')
all_weeks = pd.merge(all_weeks, teams_df, left_on='Opponent', right_on='Name',how='left')
all_weeks['Matchup1'] = (all_weeks['roster_id_x']+all_weeks['roster_id_y'])
all_weeks['Matchup'] = all_weeks['Matchup1'].astype(str)+'_'+all_weeks['Week'].astype(str)
all_weeks.drop(['roster_id_x', 'roster_id_y', 
                'Matchup1','Name_x','Name_y'], axis=1, inplace=True)

##### GET AT-BATS #####
##### GET AT-BATS #####
##### GET AT-BATS #####

all_weeks[['H', 'AB']] = all_weeks['H/AB'].str.split('/', expand=True)

##### FIX PITCHING CATEGORIES #####
##### FIX PITCHING CATEGORIES #####
##### FIX PITCHING CATEGORIES #####

all_weeks.IP = pd.to_numeric(all_weeks.IP, errors="ignore")
all_weeks['ERA'] = all_weeks.apply(lambda x: 0 if x['IP'] == 0 else x['ERA'], axis=1) 
all_weeks['WHIP'] = all_weeks.apply(lambda x: 0 if x['IP'] == 0 else x['WHIP'], axis=1) 


all_weeks['IP_DECIMAL'] = (all_weeks['IP'] - np.fix(all_weeks['IP']))*10/3
all_weeks['IP_FULL'] = np.fix(all_weeks['IP'])
all_weeks['Innings'] = all_weeks['IP_DECIMAL'] + all_weeks['IP_FULL']
all_weeks['Earned_Runs'] = all_weeks['ERA']*all_weeks['Innings']/9
all_weeks['Walk_Hits'] = all_weeks['WHIP']*all_weeks['Innings']


##### CHANGE VARIABLE FORMATS #####
##### CHANGE VARIABLE FORMATS #####
##### CHANGE VARIABLE FORMATS #####

cat_cols = [col for col in all_weeks.columns if col not in ['H/AB', 'Team','Opponent','ERA','WHIP']]
cat_cols2 = [col for col in all_weeks.columns if col in ['H/AB', 'Team','Opponent']]

for col in cat_cols:
    all_weeks[col] = all_weeks[col].astype('float')

for col in cat_cols2:
    all_weeks[col] = all_weeks[col].astype('string')


##### CREATE OBP VARIABLES #####
##### CREATE OBP VARIABLES #####
##### CREATE OBP VARIABLES #####

all_weeks['OnBase'] = (all_weeks['OBP']*all_weeks['AB']-all_weeks['H'])/(1-all_weeks['OBP'])+all_weeks['H']
all_weeks['PA'] = (all_weeks['OBP']*all_weeks['AB']-all_weeks['H'])/(1-all_weeks['OBP'])+all_weeks['AB']

all_weeks['OnBase'] = all_weeks['OnBase'].astype(int)
all_weeks['PA'] = all_weeks['PA'].astype(int)

for index, row in all_weeks.iterrows():
    while all_weeks.at[index,'OnBase']/all_weeks.at[index,'PA'] - all_weeks.at[index,'OBP'] <-0.0005 :
        all_weeks.at[index,'OnBase'] = all_weeks.at[index,'OnBase']+1
        all_weeks.at[index,'PA'] = all_weeks.at[index,'PA']+2
        all_weeks.at[index,'OBP_New'] = all_weeks.at[index,'OnBase']/all_weeks.at[index,'PA']

##### SEMIFINALS #####
##### SEMIFINALS #####
##### SEMIFINALS #####

df_semis = all_weeks.groupby(['Team'])[["OnBase", "PA","R","HR","RBI","SB","Innings","Earned_Runs","Walk_Hits","K","QS","SV+H"]].apply(lambda x : x.sum())

cat_cols = [col for col in df_semis.columns if col in ["R","HR","RBI","SB","K","QS","SV+H","OB","PA"]]

for col in cat_cols:
    df_semis[col] = df_semis[col].astype('int')

df_semis['ERA'] = df_semis['Earned_Runs']/df_semis['Innings']*9
df_semis['WHIP'] = df_semis['Walk_Hits']/df_semis['Innings']
df_semis['OBP'] = df_semis['OnBase']/df_semis['PA']

df_semis['OB/PA'] = df_semis['OnBase'].astype(str)+"/"+ df_semis['PA'].astype(str)

cols = ['OB/PA','R','HR','RBI','SB', 'OBP', 'Innings', 'K', 'ERA', 'WHIP', 'QS','SV+H']
df_semis = df_semis[cols]
df_semis.index.names = ['Team']

##### set up all matchups
matchup1 = df_semis[df_semis.index.isin(['Lumberjacks','Bryzzo'])]
matchup2 = df_semis[df_semis.index.isin(['I Shota The Sheriff','Aluminum Power'])]
matchup3 = df_semis[df_semis.index.isin(['Humdingers',"Baseball GPT"])]
matchup4 = df_semis[df_semis.index.isin(['Santos L. Halper',"El Squeezo Bunto Dos"])]
matchup5 = df_semis[df_semis.index.isin(['Frozen Ropes','Acuña Moncada'])]
matchup6 = df_semis[df_semis.index.isin(['The Chandler Mandrills','Sheangels'])]


def scores(df):
    max_val = df[['R','HR','RBI','SB','OBP','K','QS','SV+H']].max(axis=0)
    count_max = df.eq(max_val, axis=1).sum(axis=1).reset_index(name ='Total')

    min_val = df[['ERA','WHIP']].min(axis=0)
    count_min = df.eq(min_val, axis=1).sum(axis=1).reset_index(name ='Total')

    total_1 = pd.concat([count_max,count_min])
    total_1 = total_1.groupby(['Team'])[["Total"]].apply(lambda x : x.astype(int).sum())

    df = df.merge(total_1, left_on='Team', right_on='Team')

    Total = df['Total'].sum()
    if Total>10: df['Total'] = df['Total']-((Total-10)/2)
    else: df['Total'] = df['Total']

    df['Total'] = df['Total'].round(2)

    cols = ['OB/PA','R','HR','RBI','SB', 'OBP', 'Innings', 'K', 'ERA', 'WHIP', 'QS','SV+H','Total']
    df = df[cols]

    return df

matchup1, matchup2, matchup3, matchup4, matchup5, matchup6 = [scores(df) for df in (matchup1, matchup2, matchup3, matchup4, matchup5, matchup6)]


st.header("~~~~~~~~ Championship Bracket ~~~~~~~~")
st.dataframe(matchup1.style.highlight_max(subset = ['Total','R','HR','RBI', 'SB', 'OBP', 'K', 'QS', 'SV+H'], color = 'lightgreen', axis = 0)
        .highlight_min(subset = ['ERA','WHIP'], color = 'lightgreen', axis = 0).format({'ERA': "{:.2f}",'WHIP': "{:.2f}",'OBP': "{:.3f}",'Innings': "{:.2f}"}),use_container_width=True)
st.dataframe(matchup2.style.highlight_max(subset = ['Total','R','HR','RBI', 'SB', 'OBP', 'K', 'QS', 'SV+H'], color = 'lightgreen', axis = 0)
         .highlight_min(subset = ['ERA','WHIP'], color = 'lightgreen', axis = 0).format({'ERA': "{:.2f}",'WHIP': "{:.2f}",'OBP': "{:.3f}",'Innings': "{:.2f}"}),use_container_width=True)
st.dataframe(matchup3.style.highlight_max(subset = ['Total','R','HR','RBI', 'SB', 'OBP', 'K', 'QS', 'SV+H'], color = 'lightgreen', axis = 0)
         .highlight_min(subset = ['ERA','WHIP'], color = 'lightgreen', axis = 0).format({'ERA': "{:.2f}",'WHIP': "{:.2f}",'OBP': "{:.3f}",'Innings': "{:.2f}"}))
st.header("~~~~~~~~ Consoloation Bracket ~~~~~~~~")
st.dataframe(matchup4.style.highlight_max(subset = ['Total','R','HR','RBI', 'SB', 'OBP', 'K', 'QS', 'SV+H'], color = 'lightgreen', axis = 0)
         .highlight_min(subset = ['ERA','WHIP'], color = 'lightgreen', axis = 0).format({'ERA': "{:.2f}",'WHIP': "{:.2f}",'OBP': "{:.3f}",'Innings': "{:.2f}"}))
st.dataframe(matchup5.style.highlight_max(subset = ['Total','R','HR','RBI', 'SB', 'OBP', 'K', 'QS', 'SV+H'], color = 'lightgreen', axis = 0)
         .highlight_min(subset = ['ERA','WHIP'], color = 'lightgreen', axis = 0).format({'ERA': "{:.2f}",'WHIP': "{:.2f}",'OBP': "{:.3f}",'Innings': "{:.2f}"}))
st.dataframe(matchup6.style.highlight_max(subset = ['Total','R','HR','RBI', 'SB', 'OBP', 'K', 'QS', 'SV+H'], color = 'lightgreen', axis = 0)
         .highlight_min(subset = ['ERA','WHIP'], color = 'lightgreen', axis = 0).format({'ERA': "{:.2f}",'WHIP': "{:.2f}",'OBP': "{:.3f}",'Innings': "{:.2f}"}))



st.dataframe(indi_worst,hide_index=True,use_container_width=True)
