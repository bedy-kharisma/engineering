import pandas as pd
import streamlit as st
from st_aggrid import AgGrid
from st_aggrid import JsCode, GridUpdateMode, DataReturnMode
from st_aggrid.grid_options_builder import GridOptionsBuilder
import  openpyxl
import pandas as pd
import os
from streamlit import caching


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
    caching.clear_cache()
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

        
page_names_to_funcs = {
    "Product Breakdown Structure": system_requirement,
 
    
    }

selected_page = st.sidebar.radio("Select a page", page_names_to_funcs.keys())
page_names_to_funcs[selected_page]()
