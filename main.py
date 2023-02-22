import pandas as pd
import streamlit as st
from st_aggrid import AgGrid
from st_aggrid import JsCode, GridUpdateMode, DataReturnMode
from st_aggrid.grid_options_builder import GridOptionsBuilder
import  openpyxl
import pandas as pd
from streamlit import caching
import requests
import joblib
from io import BytesIO
from github import Github
import io
import base64
import pickle
from github import Github, UnknownObjectException
from google.oauth2 import service_account
from gsheetsdb import connect
import pyparsing
import gspread
from oauth2client.service_account import ServiceAccountCredentials


# Create a connection object.
#credentials = service_account.Credentials.from_service_account_info(
#    st.secrets["gcp_service_account"],
#    scopes=[
#        "https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"
#    ],
#)
#conn = connect(credentials=credentials)
credentials = ServiceAccountCredentials.from_json_keyfile_name(
    st.secrets["gcp_service_account"],
    scopes=[
            "https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"
        ],
)
client=gspread.authorize(credentials)

def run_query(query):
    rows = conn.execute(query, headers=1)
    rows = rows.fetchall()
    return rows

def validate_numeric(user_input):
    try:
        float(user_input)
        return True
    except ValueError:
        return False

def xlookup(lookup_value, lookup_array, return_array, if_not_found:str = ''):
    match_value = return_array.loc[lookup_array == lookup_value]
    if match_value.empty:
        return f'"{lookup_value}" not found!' if if_not_found == '' else if_not_found

    else:
        return match_value.tolist()[0]

def filter_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    #get types_of_train sheet id
    types_of_train='1SX8ZLJWHZv_xHQ039gL02YsQt6szFhCMZylv9PshTao'
    #convert google sheet to csv for easy handling -> types_of_train (tot)
    tot_url=(f"https://docs.google.com/spreadsheets/d/{types_of_train}/export?format=csv")
    #create dataframe from csv
    tot_df=pd.read_csv(tot_url)

    #get unique Type of Train
    unq_tot=tot_df['Type of Train'].unique()

    # Define select_tot as the selected value from selectbox
    select_tot = st.selectbox('Pilih Jenis Kereta',unq_tot)

    #filter df based on type of train selection single selectbox
    filtered_tot = tot_df[tot_df['Type of Train'] == select_tot]
    #get unique level1 based on filtered tot df
    unq_filtered_tot=filtered_tot['MPG name'].unique()

    df = df.copy()
    to_filter_columns = st.multiselect("Main Product group apa sajakah yang akan Anda gunakan", unq_filtered_tot,unq_filtered_tot,key=1)

    modification_container = st.container()
    with modification_container:

        level2 = []
        level3 = []
        
        for i in to_filter_columns: 
            left, right = st.columns((1, 20))
            left.write("↳")
            with st.expander(f"Choose Sub Sub Product group (S-SPG) on {i}"):
                user_lvl2_input = right.multiselect(
                    f"Choose Sub Product group (SPG) on {i}",
                    df.loc[df['MPG name'] == i, 'SPG name'].unique(),
                    default=df.loc[df['MPG name'] == i, 'SPG name'].unique(),key=str(i)
                )
                level2 += user_lvl2_input
                for j in user_lvl2_input: 
                    left, right = st.columns((3, 20))
                    left.write("↳↳")

                    user_lvl3_input = right.multiselect(
                        f"Choose Sub Sub Product group (S-SPG) on {j}",
                        df.loc[df['SPG name'] == j, 'sub subproduct groups'].unique(),
                        default=df.loc[df['SPG name'] == j, 'sub subproduct groups'].unique(),key=str(i+j)
                    )
                    level3 += user_lvl3_input
    df = df[df['MPG name'].isin(to_filter_columns)]
    df = df[df['SPG name'].isin(level2)]
    df = df[df['sub subproduct groups'].isin(level3)]
    st.markdown("## Berikut komponen yang Anda pilih:")
    return df

def system_requirement():
   
    st.empty()
    st.title("Product Breakdown Structure")
    st.write(
        """This app streamlines the initial engingeeing process for a railway vehicle manufacturer by allowing users to select components based on the [BS EN 15380-2-2006 standard](https://drive.google.com/file/d/1O20tY4gVVmZVUSgSxAiYVSOxFs3tg48k/view?usp=share_link). It simplifies the initial steps of RAMS, such as system requirements, selection, and design, but please note that the app is not meant to fully cover the whole process. Human supervision is still necessary to ensure accuracy.
        """
    )
    
    tab1,tab2 = st.tabs(["Product Breakdown Picker 🍒","Product Breakdown Checker ✔️"])
    with tab1:
        #get sheet id
        sheet_id='1ikMHr99Z-IGOFcwK6a5On7soFtkGSG051LrKZvM-1sA'
        #convert google sheet to csv for easy handling
        csv_url=(f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv")
        #create dataframe from csv
        df=pd.read_csv(csv_url)
        df=filter_dataframe(df)
        df.insert(2, "Qty/TS for level 1", "")
        df.insert(5, "Qty/TS for level 2", "")
        df.insert(7, "Qty/TS for level 3", "")
        df.insert(9, "Remark", "")

        gd=GridOptionsBuilder.from_dataframe(df)
        gd.configure_pagination(enabled=True)
        gd.configure_default_column(editable=True,groupable=True)
        gridoptions=gd.build()
        AgGrid(df,gridOptions=gridoptions, height=500, theme='alpine')
    with tab2:
        #get types_of_train sheet id
        types_of_train='1SX8ZLJWHZv_xHQ039gL02YsQt6szFhCMZylv9PshTao'
        #convert google sheet to csv for easy handling -> types_of_train (tot)
        tot_url=(f"https://docs.google.com/spreadsheets/d/{types_of_train}/export?format=csv")
        #create dataframe from csv
        tot_df=pd.read_csv(tot_url)

        #get unique Type of Train
        unq_tot=tot_df['Type of Train'].unique()

        # Define select_tot as the selected value from selectbox
        select_tot = st.selectbox('Pilih Jenis Kereta',unq_tot,key=str("select_tot"))

        #filter df based on type of train selection single selectbox
        filtered_tot = tot_df[tot_df['Type of Train'] == select_tot]
        #get unique level1 based on filtered tot df
        unq_filtered_tot=pd.DataFrame(filtered_tot['MPG name'].unique(),columns=['MPG name'])
        #get sheet id
        sheet_id='1ikMHr99Z-IGOFcwK6a5On7soFtkGSG051LrKZvM-1sA'
        #convert google sheet to csv for easy handling
        csv_url=(f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv")
        #create dataframe from csv
        df=pd.read_csv(csv_url)
             
        # left join with unq_filtered_tot
        joined_df = df.merge(unq_filtered_tot, on='MPG name', how='right')
        
        # Display the joined DataFrame
        gd=GridOptionsBuilder.from_dataframe(joined_df)
        gd.configure_default_column(editable=False,groupable=True)
        gridoptions=gd.build()
        AgGrid(joined_df,gridOptions=gridoptions, height=500, theme='alpine')

        uploaded_file2 = st.file_uploader("Upload a CSV or Excel file for the second dataset:", type=["csv", "xlsx"])
        if uploaded_file2 is not None:
            data2 = pd.read_csv(uploaded_file2) if uploaded_file2.type=='csv' else pd.read_excel(uploaded_file2)
        else:
            st.warning("Please upload a CSV or Excel file for the second dataset")
        if st.button("Compare Datasets"):
            # Get the data from the reference
            data1 = joined_df.iloc[:,:5]
            if data1 is not None and data2 is not None:
                # Filter the columns in dataset 2 that are not in dataset 1
                data2 = data2[data2.columns.intersection(data1.columns)]

                # Compare the datasets
                common = data1.merge(data2, on=data1.columns.tolist())
                not_in_data1 = data2[~data2.index.isin(common.index)]
                not_in_data2 = data1[~data1.index.isin(common.index)]
                # Create a DataFrame to display the results
                df = pd.DataFrame(columns=["Dataset 1", "Shared", "Not in Dataset 1", "Not in Dataset 2","Dataset 2"])
                for index in not_in_data1.index:
                    df = df.append({"Dataset 1": "", "Shared": "", "Not in Dataset 1": "✔", "Not in Dataset 2":"", "Dataset 2": not_in_data1.loc[index].values.tolist()}, ignore_index=True)

                for index in not_in_data2.index:
                    df = df.append({"Dataset 1": not_in_data2.loc[index].values.tolist(), "Shared": "", "Not in Dataset 1": "", "Not in Dataset 2": "✔", "Dataset 2":""},ignore_index=True)
                for index in common.index:
                    df = df.append({"Dataset 1": common.loc[index].values.tolist(), "Shared": "✔", "Not in Dataset 1": "", "Not in Dataset 2": "", "Dataset 2": common.loc[index].values.tolist()},ignore_index=True)

                    
                                        
            # Display the DataFrame
            gd=GridOptionsBuilder.from_dataframe(df)
            gd.configure_default_column(editable=False,groupable=True)
            gridoptions=gd.build()
            AgGrid(df,gridOptions=gridoptions, height=500, theme='alpine')

def Supplier():
    st.empty()
    #get supplier id
    Suppplier='1_Gtz3x6yNI1qAvwaFdGSggfzrdf_6TtVvcL5Ny_6wOE'
    #convert google sheet to csv for easy handling -> types_of_train (tot)
    Suppplier_url=(f"https://docs.google.com/spreadsheets/d/{Suppplier}/export?format=csv")
    #create dataframe from csv
    Suppplier_df=pd.read_csv(Suppplier_url)
    
    unq_cat=Suppplier_df['Category'].unique()
    cat=st.selectbox("Pilih Category yang ada",unq_cat)
    unq_subcat = Suppplier_df[Suppplier_df['Category'].str.contains(cat)]['SubName Category'].unique()
    subcat=st.selectbox("Pilih Sub Category yang ada",unq_subcat)
    unq_subsubcat = Suppplier_df[Suppplier_df['Category'].str.contains(cat)&Suppplier_df['SubName Category'].str.contains(subcat)]['Sub SubName category'].unique()
    subsubcat=st.selectbox("Pilih Sub SubCategory yang ada",unq_subsubcat)
    
  
    #filter
    filtered_Suppplier = Suppplier_df[Suppplier_df['Category'].str.contains(cat)&Suppplier_df['SubName Category'].str.contains(subcat)&Suppplier_df['Sub SubName category'].str.contains(subsubcat)]
   
    st.write(f"{filtered_Suppplier.shape[0]} number of supplier found using keyword : {cat} & {subcat} & {subsubcat}")
    # Display the DataFrame
    gd=GridOptionsBuilder.from_dataframe(filtered_Suppplier )
    gd.configure_pagination(enabled=True)
    gd.configure_default_column(editable=False,groupable=True)
    gridoptions=gd.build()
    AgGrid(filtered_Suppplier ,gridOptions=gridoptions, height=500, theme='alpine')

def Standards():
    st.empty()
    # Define the URL of the file on the public GitHub repository
    file_url = 'https://raw.githubusercontent.com/bedy-kharisma/engineering/main/standards.pkl'
    # Download the file contents from the URL
    response = requests.get(file_url)
    if response.status_code == 200:
        content = BytesIO(response.content)
   
        standards = pd.read_pickle(content)
        keyword = st.text_input('Pilih keyword yang ingin Anda cari')
        #filter
        filtered_std = standards[standards['text'].str.contains(keyword)]
        standards_df=filtered_std[["location","name","id"]]
        if keyword!="":
            st.write(f"{standards_df.shape[0]} number of standards found using keyword : {keyword}")

        # Display the DataFrame
        gd=GridOptionsBuilder.from_dataframe(standards_df)
        gd.configure_column("id", headerName="id", cellRenderer=JsCode('''function(params) {return '<a href="https://drive.google.com/file/d/' + params.value + '/view" target="_blank">' + params.value + '</a>'}'''),
                        width=300)
        gridoptions=gd.build()

        AgGrid(standards_df, gridOptions=gridoptions, allow_unsafe_jscode=True, height=500, theme='alpine')

def FMECA():
    st.empty()
    uploaded_file2 = st.file_uploader("Upload a CSV or Excel file of Product Breakdown Structure:", type=["csv", "xlsx"])
    if uploaded_file2 is not None:
        data1 = pd.read_csv(uploaded_file2) if uploaded_file2.type=='csv' else pd.read_excel(uploaded_file2)
        #get types_of_train sheet id
        FMECA='18wTCYGDmtYUVJ5WBb_lrG-J6jY-O44v_Pl2G4mnyuxY'
        #convert google sheet to csv for easy handling -> types_of_train (tot)
        FMECA_url=(f"https://docs.google.com/spreadsheets/d/{FMECA}/export?format=csv")
        #create dataframe from csv
        FMECA_df=pd.read_csv(FMECA_url)
        # Filter the columns in dataset A to match the first 5 columns of dataset B
        columns_to_keep = FMECA_df.columns[:5]
        data1 = data1[data1.columns.intersection(FMECA_df.columns)]
        filter1 = FMECA_df["MPG name"].isin(data1["MPG name"])
        filter2 = FMECA_df["SPG name"].isin(data1["SPG name"])
        filter3 = FMECA_df["sub subproduct groups"].isin(data1["sub subproduct groups"])
        
        merged_df=FMECA_df[filter1&filter2&filter3]
        
    else:
        st.warning("Please upload a CSV or Excel file for the second dataset") 
   
   
    if st.button("Generate initial FMECA") and uploaded_file2 is not None:
        # Display the DataFrame
        gd=GridOptionsBuilder.from_dataframe(merged_df)
        gd.configure_pagination(enabled=True)
        gd.configure_default_column(editable=False,groupable=True)
        gridoptions=gd.build()
        AgGrid(merged_df,gridOptions=gridoptions, height=500, theme='alpine')

def failure():
    st.empty()
    #get sheet id
    sheet_id='1yYY6kEVkBRRdmNcGG1cG2F3gbPA_OZJ5rUTWahx5X-U'
    #convert google sheet to csv for easy handling
    csv_url=(f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv")
    #create dataframe from csv
    df=pd.read_csv(csv_url)
    unq_mainsys=df['Main System'].unique()
    df['Jumlah kegagalan']= df['Jumlah kegagalan'].astype(int)

    st.markdown("# Failure Rate Calculator")
    st.write("This failure rate calcuator is populated using database saved in this [google sheet](https://docs.google.com/spreadsheets/d/1yYY6kEVkBRRdmNcGG1cG2F3gbPA_OZJ5rUTWahx5X-U/edit?usp=sharing)")
    mainsys = st.selectbox('Pilih Main System apa yang akan Anda hitung',unq_mainsys)
    #filter df based on main system selection single selectbox
    filtered_df = df[df['Main System'] == mainsys]
    #get unique project name based on filtered df
    unq_proj=filtered_df['Project Name'].unique()
    proj = st.multiselect('Data dari Project saja yang akan Anda gunakan',unq_proj,unq_proj)
    #filter df based on multiple selection project name
    filtered_df = filtered_df[filtered_df['Project Name'].isin(proj)]
    #get unique vendor based on above filtered df
    unq_vendor=filtered_df['Vendor Name'].unique()
    vendor=st.multiselect('Data dari Vendor saja yang akan Anda gunakan',unq_vendor,unq_vendor)
    #filter based on multiple select vendor name
    filtered_df = filtered_df[filtered_df['Vendor Name'].isin(vendor)]

    # Create a new dataframe with the duplicates removed
    df_no_duplicates = filtered_df.drop_duplicates(subset='Project Name', inplace=False)
    # sum the values in the 'operating hours per year' column
    total_ophours = df_no_duplicates['Operating Hours per Year'].sum()
    # Assign the sum back to the original dataframe
    filtered_df['Total Operating Hours'] = total_ophours.astype(int)

    #calculate total quantity
    filtered_df['Total Quantity'] = filtered_df.groupby('Item Name')['Quantity all Trainset'].transform('sum')
    filtered_df['Total Quantity']= filtered_df['Total Quantity'].astype(int)

    #calculate t = Total komponen*OH
    filtered_df['Total komponen*OH']= filtered_df['Total Quantity']*filtered_df['Total Operating Hours']
    filtered_df['Total komponen*OH']= filtered_df['Total komponen*OH']

    # Define the function
    def failure_rate(row):
        if row['Total Quantity'] == 0 or row['Total Operating Hours'] == 0:
            return 0
        if row['Jumlah kegagalan'] > 0:
            return row['Jumlah kegagalan'] / row['Total komponen*OH']
        else:
            return 1 / (row['Total Quantity'] * row['Total Operating Hours'])
    # Apply the function to the dataframe
    filtered_df['Failure Rate'] = filtered_df.apply(failure_rate, axis=1)

    #change into scientific format
    def to_scientific(x):
        return '{:.2e}'.format(x)
    filtered_df['Failure Rate'] = filtered_df['Failure Rate'].apply(to_scientific)

    #show only unique item
    unique_df = filtered_df.drop_duplicates(subset=['Item Ref', 'Item Name'])
    unique_df  = unique_df .reset_index().drop(columns='index')
    st.dataframe(unique_df[['Item Ref', 'Item Name','Total Operating Hours','Total Quantity','Jumlah kegagalan','Failure Rate']])

def FBS():
    st.empty()
    st.title("Function Breakdown Structure")
    st.write(
        """This app streamlines the initial engingeeing process for a railway vehicle manufacturer by allowing users to select functions based on the [BS EN 15380-4-2013 standard](https://drive.google.com/file/d/19Wmq1jLGlQdNZL9UpnUgL80Ec5c-gC1M/view?usp=share_link). It simplifies the initial steps of RAMS, such as system requirements, selection, and design, but please note that the app is not meant to fully cover the whole process. Human supervision is still necessary to ensure accuracy.
        """
    )
    
    tab1,tab2 = st.tabs(["Function Breakdown Picker 🍒","Function Breakdown Checker ✔️"])
    with tab1:
        #get sheet id level1-3 FBS
        sheet_id='1yEtUmBuxRewIiclGothFn9IaZdgm458owf8V_ZJnYQk'
        #convert google sheet to csv for easy handling
        csv_url=(f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv")
        #create dataframe from csv
        fbs_df=pd.read_csv(csv_url,on_bad_lines='skip')
        ##################
        to_filter_columns = st.multiselect("Function Level 1 apa sajakah yang akan Anda gunakan", fbs_df['level 1 Function'].unique(),fbs_df['level 1 Function'].unique(),key=1)

        modification_container = st.container()
        with modification_container:

            level2 = []
            level3 = []

            for i in to_filter_columns: 
                if pd.isna(i):
                    continue
                left, right = st.columns((1, 20))
                left.write("↳")
                with st.expander(f"Choose Level 3 Function group on {i}"):
                    user_lvl2_input = right.multiselect(
                        f"Choose Level 2 Function group on {i}",
                        fbs_df.loc[fbs_df['level 1 Function'] == i, 'level 2 Function'].dropna().unique(),
                        default=fbs_df.loc[fbs_df['level 1 Function'] == i, 'level 2 Function'].dropna().unique(),key=str(i)
                    )
                    level2 += user_lvl2_input
                    for j in user_lvl2_input: 
                        if pd.isna(j):
                            continue
                        left, right = st.columns((3, 20))
                        left.write("↳↳")

                        user_lvl3_input = right.multiselect(
                            f"Choose Level 3 Function on {j}",
                            fbs_df.loc[fbs_df['level 2 Function'] == j, 'level 3 Function'].dropna().unique(),
                            default=fbs_df.loc[fbs_df['level 2 Function'] == j, 'level 3 Function'].dropna().unique(),key=str(i) + str(j)
                        )
                        level3 += user_lvl3_input
        fbs_df = fbs_df[fbs_df['level 1 Function'].isin(to_filter_columns)]
        fbs_df = fbs_df[fbs_df['level 2 Function'].isin(level2)]
        fbs_df = fbs_df[fbs_df['level 3 Function'].isin(level3)]
        st.markdown("## Berikut Functions yang Anda pilih:")
    
        gd=GridOptionsBuilder.from_dataframe(fbs_df)
        gd.configure_default_column(editable=True,groupable=True)
        gridoptions=gd.build()
        AgGrid(fbs_df,gridOptions=gridoptions, height=800, theme='alpine')
        
    with tab2:
        #get sheet id level1-3 FBS
        sheet_id='1yEtUmBuxRewIiclGothFn9IaZdgm458owf8V_ZJnYQk'
        #convert google sheet to csv for easy handling
        csv_url=(f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv")
        #create dataframe from csv
        fbs_df=pd.read_csv(csv_url,on_bad_lines='skip')
        ##################
        
        # Display the joined DataFrame
        gd=GridOptionsBuilder.from_dataframe(fbs_df)
        gd.configure_default_column(editable=False,groupable=True)
        gridoptions=gd.build()
        AgGrid(fbs_df,gridOptions=gridoptions, height=500, theme='alpine')

        uploaded_file2 = st.file_uploader("Upload a CSV or Excel file for the second dataset:", type=["csv", "xlsx"])
        if uploaded_file2 is not None:
            data2 = pd.read_csv(uploaded_file2) if uploaded_file2.type=='csv' else pd.read_excel(uploaded_file2)
        else:
            st.warning("Please upload a CSV or Excel file for the second dataset")
        if st.button("Compare Datasets"):
            # Get the data from the reference
            data1 = fbs_df.iloc[:,:5]
            if data1 is not None and data2 is not None:
                # Filter the columns in dataset 2 that are not in dataset 1
                data2 = data2[data2.columns.intersection(data1.columns)]

                # Compare the datasets
                common = data1.merge(data2, on=data1.columns.tolist())
                not_in_data1 = data2[~data2.index.isin(common.index)]
                not_in_data2 = data1[~data1.index.isin(common.index)]
                # Create a DataFrame to display the results
                df = pd.DataFrame(columns=["Dataset 1", "Shared", "Not in Dataset 1", "Not in Dataset 2","Dataset 2"])
                for index in not_in_data1.index:
                    df = df.append({"Dataset 1": "", "Shared": "", "Not in Dataset 1": "✔", "Not in Dataset 2":"", "Dataset 2": not_in_data1.loc[index].values.tolist()}, ignore_index=True)

                for index in not_in_data2.index:
                    df = df.append({"Dataset 1": not_in_data2.loc[index].values.tolist(), "Shared": "", "Not in Dataset 1": "", "Not in Dataset 2": "✔", "Dataset 2":""},ignore_index=True)
                for index in common.index:
                    df = df.append({"Dataset 1": common.loc[index].values.tolist(), "Shared": "✔", "Not in Dataset 1": "", "Not in Dataset 2": "", "Dataset 2": common.loc[index].values.tolist()},ignore_index=True)
                                        
            # Display the DataFrame
            gd=GridOptionsBuilder.from_dataframe(df)
            gd.configure_default_column(editable=False,groupable=True)
            gridoptions=gd.build()
            AgGrid(df,gridOptions=gridoptions, height=500, theme='alpine')

def Matcod():
   
    pickle_file = 'database_df.pkl'
    file_url = 'https://raw.githubusercontent.com/bedy-kharisma/engineering/main/'+ pickle_file
    response = requests.get(file_url)
    if response.status_code == 200:
        content = BytesIO(response.content)
        database_df=pd.read_pickle(content) 

    pickle_file = 'TB1_df.pkl'
    file_url = 'https://raw.githubusercontent.com/bedy-kharisma/engineering/main/'+ pickle_file
    response = requests.get(file_url)
    if response.status_code == 200:
        content = BytesIO(response.content) 
        TB1_df=pd.read_pickle(content) 

    pickle_file = 'TB2_df.pkl'   
    file_url = 'https://raw.githubusercontent.com/bedy-kharisma/engineering/main/'+ pickle_file
    response = requests.get(file_url)
    if response.status_code == 200:
        content = BytesIO(response.content) 
        TB2_df=pd.read_pickle(content) 

    pickle_file = 'Fastening_df.pkl' 
    file_url = 'https://raw.githubusercontent.com/bedy-kharisma/engineering/main/'+ pickle_file
    response = requests.get(file_url)
    if response.status_code == 200:
        content = BytesIO(response.content) 
        Fastening_df=pd.read_pickle(content) 

    pickle_file = 'maincom_df.pkl'
    file_url = 'https://raw.githubusercontent.com/bedy-kharisma/engineering/main/'+ pickle_file
    response = requests.get(file_url)
    if response.status_code == 200:
        content = BytesIO(response.content) 
        maincom_df=pd.read_pickle(content) 

    pickle_file = 'sw_df.pkl' 
    file_url = 'https://raw.githubusercontent.com/bedy-kharisma/engineering/main/'+ pickle_file
    response = requests.get(file_url)
    if response.status_code == 200:
        content = BytesIO(response.content)
        sw_df=pd.read_pickle(content) 

    pickle_file = 'el_df.pkl'
    file_url = 'https://raw.githubusercontent.com/bedy-kharisma/engineering/main/'+ pickle_file
    response = requests.get(file_url)
    if response.status_code == 200:
        content = BytesIO(response.content)
        el_df=pd.read_pickle(content) 

    pickle_file = 'brake_df.pkl'
    file_url = 'https://raw.githubusercontent.com/bedy-kharisma/engineering/main/'+ pickle_file
    response = requests.get(file_url)
    if response.status_code == 200:
        content = BytesIO(response.content)
        brake_df=pd.read_pickle(content) 

    pickle_file = 'bogie_df.pkl'
    file_url = 'https://raw.githubusercontent.com/bedy-kharisma/engineering/main/'+ pickle_file
    response = requests.get(file_url)
    if response.status_code == 200:
        content = BytesIO(response.content)
        bogie_df=pd.read_pickle(content) 

    pickle_file = 'coupler_df.pkl'    
    file_url = 'https://raw.githubusercontent.com/bedy-kharisma/engineering/main/'+ pickle_file
    response = requests.get(file_url)
    if response.status_code == 200:
        content = BytesIO(response.content)
        coupler_df=pd.read_pickle(content) 

    pickle_file = 'interior_df.pkl'
    file_url = 'https://raw.githubusercontent.com/bedy-kharisma/engineering/main/'+ pickle_file
    response = requests.get(file_url)
    if response.status_code == 200:
        content = BytesIO(response.content)
        interior_df=pd.read_pickle(content) 

    pickle_file = 'piping_df.pkl'
    file_url = 'https://raw.githubusercontent.com/bedy-kharisma/engineering/main/'+ pickle_file
    response = requests.get(file_url)
    if response.status_code == 200:
        content = BytesIO(response.content)
        piping_df=pd.read_pickle(content)

    pickle_file = 'cons_df.pkl'
    file_url = 'https://raw.githubusercontent.com/bedy-kharisma/engineering/main/'+ pickle_file
    response = requests.get(file_url)
    if response.status_code == 200:
        content = BytesIO(response.content)
        cons_df=pd.read_pickle(content)

    pickle_file = 'tools_df.pkl'
    file_url = 'https://raw.githubusercontent.com/bedy-kharisma/engineering/main/'+ pickle_file
    response = requests.get(file_url)
    if response.status_code == 200:
        content = BytesIO(response.content)
        tools_df=pd.read_pickle(content)

    pickle_file = 'raw_df.pkl' 
    file_url = 'https://raw.githubusercontent.com/bedy-kharisma/engineering/main/'+ pickle_file
    response = requests.get(file_url)
    if response.status_code == 200:
        content = BytesIO(response.content)
        raw_df=pd.read_pickle(content)

    pickle_file = 'spare_df.pkl'
    file_url = 'https://raw.githubusercontent.com/bedy-kharisma/engineering/main/'+ pickle_file
    response = requests.get(file_url)
    if response.status_code == 200:
        content = BytesIO(response.content)
        spare_df=pd.read_pickle(content)

    pickle_file = 'facilities_df.pkl'
    file_url = 'https://raw.githubusercontent.com/bedy-kharisma/engineering/main/'+ pickle_file
    response = requests.get(file_url)
    if response.status_code == 200:
        content = BytesIO(response.content)
        facilities_df=pd.read_pickle(content)

    st.title("MATERIAL CODE")
    tab1, tab2 = st.tabs(["Request", "Verification"])
    with tab1:

        # Display the DataFrame
        gd=GridOptionsBuilder.from_dataframe(database_df )
        gd.configure_pagination(enabled=True)
        gd.configure_default_column(editable=False,groupable=True)
        gridoptions=gd.build()
        AgGrid(database_df ,gridOptions=gridoptions, height=500, theme='alpine')
        st.write("### If you are sure that what you are looking for is not listed there, please fill up the entry form below:")
        #get unique
        unq_TB1=TB1_df['NAMA'].unique()
        # Define select as the selected value from selectbox
        select_TB1 = st.selectbox('Choose TB1 Code',unq_TB1)
        select_TB1 = xlookup(select_TB1, TB1_df['NAMA'],TB1_df['CODE'])
        st.write(select_TB1)
        #filter TB2 based on type of train selection single selectbox
        filtered_TB2 = TB2_df[TB2_df['CODE_TB1'].str.contains(select_TB1, na=False)]

        unq_TB2=filtered_TB2['NAMA'].unique()

        # Define select as the selected value from selectbox
        select_TB2 = st.selectbox('Choose TB2 Code',unq_TB2)
        select_TB2 = xlookup(select_TB2, TB2_df['NAMA'],TB2_df['CODE_TB2'])

        code=select_TB1+select_TB2
        st.write(code)
        df_dict = {"A54": el_df,"A52": el_df,"B39": Fastening_df, "B40": maincom_df, "B54": sw_df, "B52": el_df, "B47": brake_df, "B48": bogie_df, "B49": coupler_df, "B50": interior_df, "B51": piping_df, "D29": cons_df, "D30": cons_df, "D31": cons_df, "D32": cons_df, "D33": cons_df, "D61": cons_df, "D62": cons_df, "D63": cons_df, "D64": cons_df, "D65": cons_df, "D66": cons_df, "D67": cons_df, "D68": cons_df, "D69": cons_df, "D70": cons_df, "D71": cons_df, "D72": cons_df, "D73": cons_df, "D74": cons_df, "D75": cons_df, "D76": cons_df, "D80": cons_df, "D82": cons_df, "D83": cons_df, "D84": cons_df, "D98": cons_df, "D99": cons_df, "C71": tools_df, "C77": tools_df, "C78": tools_df, "C79": tools_df, "C85": tools_df, "C86": tools_df, "C87": tools_df, "C88": tools_df, "C89": tools_df, "C90": tools_df, "C91": tools_df, "C92": tools_df, "C93": tools_df, "C94": tools_df, "C95": tools_df, "C96": tools_df, "A01": raw_df, "A04": raw_df, "A09": raw_df, "A10": raw_df, "A11": raw_df, "A12": raw_df, "A13": raw_df, "A14": raw_df, "A15": raw_df, "A16": raw_df, "A17": raw_df, "A18": raw_df, "A19": raw_df, "A20": raw_df, "A21": raw_df, "A22": raw_df, "A23": raw_df, "A24": raw_df, "A25": raw_df, "B98": spare_df, "D98": spare_df, "E97": facilities_df}

        skip_codes = ["B37", "B41", "B42", "B43", "B44","B45", "B46"]

        if code not in skip_codes:
            selected_df = df_dict[code]
            if selected_df is not None:
                gd=GridOptionsBuilder.from_dataframe(selected_df)
                gd.configure_pagination(enabled=False)
                gd.configure_default_column(editable=False,groupable=True)
                gridoptions=gd.build()
                AgGrid(selected_df ,gridOptions=gridoptions, height=500, theme='alpine', fit_columns_on_grid_load=True)
                unq_selected_df=selected_df['DESCRIPTION'].unique()
                select_TB3 = st.selectbox('Choose TB3 Description',unq_selected_df)
                select_TB3 = xlookup(select_TB3, selected_df['DESCRIPTION'],selected_df['CODE'])
                code=select_TB1+select_TB2+select_TB3
                st.write(code)
                df = database_df[database_df["Kode Material"].str[:7].isin([code])]
        else:
                code=select_TB1+select_TB2
                df = database_df[database_df["Kode Material"].str[:3].isin([code])]
        # Display the DataFrame
        gd=GridOptionsBuilder.from_dataframe(df)
        gd.configure_pagination(enabled=False)
        gd.configure_default_column(editable=False,groupable=True)
        gridoptions=gd.build()
        AgGridaggrid = AgGrid(df, gridOptions=gridoptions, height=500, theme='alpine', 
                         data_return_mode=DataReturnMode.AS_INPUT, update_on='VALUE_CHANGED',        
                         enable_enterprise_modules=True, update_mode=GridUpdateMode.SELECTION_CHANGED,
                         allow_unsafe_jscode=True, fit_columns_on_grid_load=True)

        st.write("### If you are sure that what you are looking for is not listed there, please fill up the entry form below:")

        user_input = st.text_input("Insert unique number id", "",max_chars=7, key="input")
        if validate_numeric(user_input) and (len(code+user_input)<=12):
            st.write("New Material Code :")
            value_to_check=code+user_input
            if value_to_check in database_df["Kode Material"].unique():
                st.write(f'{value_to_check} is not unique in the material code database.')
            else:
                st.write(f'{value_to_check} is unique in the material code database.')
                with st.form("entry",clear_on_submit=True):
                    deskripsi = st.text_input("Insert description")
                    spec = st.text_input("Insert specification")
                    uom = st.text_input("Insert UoM")
                    requester = st.text_input("Insert Requester ID")
                    submit= st.form_submit_button("Submit")
                if submit:
                    database_df = database_df.append({'Kode Material': code+user_input, 'Deskripsi': deskripsi, 'Specification':   spec,'UoM':  uom,'Requester':   requester, 'Verification Status': "Unverified"}, ignore_index=True)    
                    sheet_url = st.secrets["private_gsheets_url"]
                    sheet=client.open("database").Sheet1
                    sheet.update([database_df.columns.values.tolist()]+database_df.values.tolist())
                    #rows = run_query(f'SELECT * FROM "{sheet_url}"')
                    #for row in rows:
                    #    st.write(f"{row.name} has a :{row.pet}:")


        else:
            st.write('Please enter a numeric value only & make sure the length is <= 12 characters')


            
    with tab2:
        password=st.text_input("Insert admin password","",type="password")
        if password == "admin":
            funct=st.radio(label="Functions:", options=['Edit','Delete'])
            if funct =='Delete':
                js=JsCode("""
                    function(e) {
                        let api = e.api;
                        let sel = api.getSelectedRows();
                        api.applyTransaction({remove: sel})
                    };
                """)

                # Display the DataFrame
                gd=GridOptionsBuilder.from_dataframe(database_df)
                gd.configure_selection(selection_mode='single',use_checkbox=True)
                gd.configure_grid_options(onRowSelected=js,pre_selected_rows=[])
                gd.configure_pagination(enabled=False)
                gd.configure_default_column(editable=True,groupable=True)
                gridoptions=gd.build()
                aggrid = AgGrid(database_df, gridOptions=gridoptions, height=500, theme='alpine', 
                         data_return_mode=DataReturnMode.AS_INPUT, update_on='VALUE_CHANGED',        
                         enable_enterprise_modules=True, update_mode=GridUpdateMode.SELECTION_CHANGED,
                         allow_unsafe_jscode=True, fit_columns_on_grid_load=True)

                # Update the original DataFrame
                data=aggrid['data']
                database_df=pd.DataFrame(data)
                
                st.info("Total rows :"+str(len(database_df)))
                #g = Github("bedy-kharisma","miupiu19")
                #repo = g.get_repo("bedy-kharisma/engineering")
                #contents = repo.get_contents('database_df.pkl')
                #new_content = pickle.dumps(database_df)
                #repo.update_file(contents.path, "update", new_content, contents.sha)
                #st.experimental_rerun()

            if funct =='Edit':
                # Display the DataFrame
                gd=GridOptionsBuilder.from_dataframe(database_df)
                gd.configure_pagination(enabled=False)
                gd.configure_default_column(editable=True,groupable=True)
                gridoptions=gd.build()
                aggrid = AgGrid(database_df ,gridOptions=gridoptions, height=500, theme='alpine', 
                                data_return_mode=DataReturnMode.AS_INPUT, update_on='VALUE_CHANGED',
                                fit_columns_on_grid_load=True)
                # Update the original DataFrame
                data=aggrid['data']
                database_df=pd.DataFrame(data)
                st.info("Total rows :"+str(len(database_df)))
                #g = Github("bedy-kharisma","miupiu19")
                #repo = g.get_repo("bedy-kharisma/engineering")
                #contents = repo.get_contents('database_df.pkl')
                #new_content = pickle.dumps(database_df)
                #repo.update_file(contents.path, "update", new_content, contents.sha)
                #st.experimental_rerun()


page_names_to_funcs = {
    "Product Breakdown Structure": system_requirement,
    "Material Code":Matcod,
    "Initial FMECA":FMECA,
    "Failure Rate Calculator":failure,
    "Function Breakdown Structure":FBS,
    "Standards finder":Standards,
    "Possible Supplier":Supplier,
    
    }

selected_page = st.sidebar.radio("Select a page", page_names_to_funcs.keys())
page_names_to_funcs[selected_page]()
