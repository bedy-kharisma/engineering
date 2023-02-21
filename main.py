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

def FMECA():
    caching.clear_cache()
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


def Standards():
    caching.clear_cache()
    standards = pd.read_pickle('./standards.pkl')
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

    
def Supplier():
    caching.clear_cache()
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
    
def Matcod():
    caching.clear_cache()
    pickle_file = 'database_df.pkl'    
    if os.path.exists(pickle_file):
        database_df=pd.read_pickle("./database_df.pkl")  
    else:
        #get database
        database_id='1uFfcegQlGi6vKtyuhq_RxDKRJ26fw_bGod2Lic5Bjy8'
        #convert google sheet to csv for easy handling
        database_url=(f"https://docs.google.com/spreadsheets/d/{database_id}/export?format=csv")
        #create dataframe from csv
        database_df=pd.read_csv(database_url).astype(str)
        database_df.to_pickle("./database_df.pkl")  

    pickle_file = 'TB1_df.pkl'    
    if os.path.exists(pickle_file):
        TB1_df=pd.read_pickle("./TB1_df.pkl") 
    else:
        #get TB1
        TB1_id='10GG3ockk965nwCLKd3K8gkbRUhLl1RGNpmTAM-tALQM'
        #convert google sheet to csv for easy handling
        TB1_url=(f"https://docs.google.com/spreadsheets/d/{TB1_id}/export?format=csv")
        #create dataframe from csv
        TB1_df=pd.read_csv(TB1_url).astype(str)
        TB1_df.to_pickle("./TB1_df.pkl")

    pickle_file = 'TB2_df.pkl'    
    if os.path.exists(pickle_file):
        TB2_df=pd.read_pickle("./TB2_df.pkl") 
    else:
        #get TB2
        TB2_id='1oU83QnuIi6I0BkfYqykLSIzXhjO4iVCRspLCcpBWtco'
        #convert google sheet to csv for easy handling
        TB2_url=(f"https://docs.google.com/spreadsheets/d/{TB2_id}/export?format=csv")
        #create dataframe from csv
        TB2_df=pd.read_csv(TB2_url).astype(str)
        TB2_df['CODE_TB2'] = TB2_df['CODE_TB2'].apply(lambda x: '0' + str(x) if len(str(x)) == 1 else x)
        TB2_df.to_pickle("./TB2_df.pkl")

    pickle_file = 'Fastening_df.pkl'    
    if os.path.exists(pickle_file):
        Fastening_df=pd.read_pickle("./Fastening_df.pkl") 
    else:    
        #get Fastening
        Fastening_id='1MU23AMrF0aRtNgRQahKHceCnGKAcUCVivv2B2fsqnrc'
        #convert google sheet to csv for easy handling
        Fastening_url=(f"https://docs.google.com/spreadsheets/d/{Fastening_id}/export?format=csv")
        #create dataframe from csv
        Fastening_df=pd.read_csv(Fastening_url).astype(str)
        Fastening_df.to_pickle("./Fastening_df.pkl")

    pickle_file = 'maincom_df.pkl'    
    if os.path.exists(pickle_file):
        maincom_df=pd.read_pickle("./maincom_df.pkl")
    else:        
        #get Main Component
        maincom_id='1LFAblU34dnIBY9jH8xvLiGQNhT88QbTi3lxUSEvmjV0'
        #convert google sheet to csv for easy handling
        maincom_url=(f"https://docs.google.com/spreadsheets/d/{maincom_id}/export?format=csv")
        #create dataframe from csv
        maincom_df=pd.read_csv(maincom_url).astype(str)
        maincom_df.to_pickle("./maincom_df.pkl")

    pickle_file = 'sw_df.pkl'    
    if os.path.exists(pickle_file):
        sw_df=pd.read_pickle("./sw_df.pkl")
    else:       
        #get Software
        sw_id='1gVFaAuapPgT4E0uVfwhj0o1yf_gmjcYBye5mLNbeHc4'
        #convert google sheet to csv for easy handling
        sw_url=(f"https://docs.google.com/spreadsheets/d/{sw_id}/export?format=csv")
        #create dataframe from csv
        sw_df=pd.read_csv(sw_url)
        sw_df.to_pickle("./sw_df.pkl")

    pickle_file = 'el_df.pkl'    
    if os.path.exists(pickle_file):
        el_df=pd.read_pickle("./el_df.pkl")
    else:       
        #get electric
        el_id='1D9dtmmNBJeOF9BVTZ-d2HerT4smAOoC4zcbd2YkTiAk'
        #convert google sheet to csv for easy handling
        el_url=(f"https://docs.google.com/spreadsheets/d/{el_id}/export?format=csv")
        #create dataframe from csv
        el_df=pd.read_csv(el_url).astype(str)
        el_df.to_pickle("./el_df.pkl")

    pickle_file = 'brake_df.pkl'    
    if os.path.exists(pickle_file):
        brake_df=pd.read_pickle("./brake_df.pkl")
    else:           
        #get brake
        brake_id='1cwtya-w8FqklV3kn8ImD_qtNOJ6ZAp4HIFhVJVGHMgs'
        #convert google sheet to csv for easy handling
        brake_url=(f"https://docs.google.com/spreadsheets/d/{brake_id}/export?format=csv")
        #create dataframe from csv
        brake_df=pd.read_csv(brake_url).astype(str)
        brake_df.to_pickle("./brake_df.pkl")

    pickle_file = 'bogie_df.pkl'    
    if os.path.exists(pickle_file):
        bogie_df=pd.read_pickle("./bogie_df.pkl")
    else:      
        #get bogie
        bogie_id='1uVeyWMDLbaig75eCTIIW5ItLItWg-Oj7frtY2Y7Dz-8'
        #convert google sheet to csv for easy handling
        bogie_url=(f"https://docs.google.com/spreadsheets/d/{bogie_id}/export?format=csv")
        #create dataframe from csv
        bogie_df=pd.read_csv(bogie_url).astype(str)
        bogie_df.to_pickle("./bogie_df.pkl")

    pickle_file = 'coupler_df.pkl'    
    if os.path.exists(pickle_file):
        coupler_df=pd.read_pickle("./coupler_df.pkl")
    else:          
        #get Coupler and Underframe
        coupler_id='12hWbb6GZcJlFNp06YIlHiTOQHB0oEca3Zg74DkPgVfg'
        #convert google sheet to csv for easy handling
        coupler_url=(f"https://docs.google.com/spreadsheets/d/{coupler_id}/export?format=csv")
        #create dataframe from csv
        coupler_df=pd.read_csv(coupler_url).astype(str)
        coupler_df.to_pickle("./coupler_df.pkl")

    pickle_file = 'interior_df.pkl'    
    if os.path.exists(pickle_file):
        interior_df=pd.read_pickle("./interior_df.pkl")
    else:         
        #get Interior exterior
        interior_id='1QQedCoQ61nzktzXnXvj_qa9eGi45mPSl9_9H28qCdjM'
        #convert google sheet to csv for easy handling
        interior_url=(f"https://docs.google.com/spreadsheets/d/{interior_id}/export?format=csv")
        #create dataframe from csv
        interior_df=pd.read_csv(interior_url).astype(str)
        interior_df.to_pickle("./interior_df.pkl")

    pickle_file = 'piping_df.pkl'    
    if os.path.exists(pickle_file):
        piping_df=pd.read_pickle("./piping_df.pkl")
    else:             
        #get piping
        piping_id='12r8bkiaFJFyDRPz68YmwDlO13xx8qzkgKqdcSIzcYFk'
        #convert google sheet to csv for easy handling
        piping_url=(f"https://docs.google.com/spreadsheets/d/{piping_id}/export?format=csv")
        #create dataframe from csv
        piping_df=pd.read_csv(piping_url).astype(str)
        piping_df.to_pickle("./piping_df.pkl")

    pickle_file = 'cons_df.pkl'    
    if os.path.exists(pickle_file):
        cons_df=pd.read_pickle("./cons_df.pkl")
    else:        
        #get Consumables
        cons_id='1mcSJlCxtQTbNyc6vRTdeaPAXECnz8IkM8iopPuDcKKg'
        #convert google sheet to csv for easy handling
        cons_url=(f"https://docs.google.com/spreadsheets/d/{cons_id}/export?format=csv")
        #create dataframe from csv
        cons_df=pd.read_csv(cons_url).astype(str)
        cons_df.to_pickle("./cons_df.pkl")

    pickle_file = 'tools_df.pkl'    
    if os.path.exists(pickle_file):
        tools_df=pd.read_pickle("./tools_df.pkl")
    else:     
        #get tools
        tools_id='1zorHM3QuRyXDTxIymSVZt8_fRdY-Xc0en6CXOVD3_Xc'
        #convert google sheet to csv for easy handling
        tools_url=(f"https://docs.google.com/spreadsheets/d/{tools_id}/export?format=csv")
        #create dataframe from csv
        tools_df=pd.read_csv(tools_url).astype(str)
        tools_df.to_pickle("./tools_df.pkl")

    pickle_file = 'raw_df.pkl'    
    if os.path.exists(pickle_file):
        raw_df=pd.read_pickle("./raw_df.pkl")
    else:     
        #get Raw mat
        raw_id='1QvWAV9kI6SQEZjaO0SWH_HJTk9NweNpIn8P8VQjfAb8'
        #convert google sheet to csv for easy handling
        raw_url=(f"https://docs.google.com/spreadsheets/d/{raw_id}/export?format=csv")
        #create dataframe from csv
        raw_df=pd.read_csv(raw_url).astype(str)
        raw_df.to_pickle("./raw_df.pkl")

    pickle_file = 'spare_df.pkl'    
    if os.path.exists(pickle_file):
        spare_df=pd.read_pickle("./spare_df.pkl")
    else:        
        #get spare part
        spare_id='1VHrcH3as8EXFofKhyuff4Qvv152WZ4HegozS1GhVNiQ'
        #convert google sheet to csv for easy handling
        spare_url=(f"https://docs.google.com/spreadsheets/d/{spare_id}/export?format=csv")
        #create dataframe from csv
        spare_df=pd.read_csv(spare_url).astype(str)
        spare_df.to_pickle("./spare_df.pkl")

    pickle_file = 'facilities_df.pkl'    
    if os.path.exists(pickle_file):
        facilities_df=pd.read_pickle("./facilities_df.pkl")
    else:     
        #get facilities
        facilities_id='11CVbivlNnNJhyN-quU0WrsGs60tPer0RIqnxJHV1Iuc'
        #convert google sheet to csv for easy handling
        facilities_url=(f"https://docs.google.com/spreadsheets/d/{facilities_id}/export?format=csv")
        #create dataframe from csv
        facilities_df=pd.read_csv(facilities_url).astype(str)
        facilities_df.to_pickle("./facilities_df.pkl")

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

        #71 cons or tools?
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
                    database_df.to_pickle("./database_df.pkl" )
                    st.experimental_rerun()

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
                database_df.to_pickle("./database_df.pkl" )

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
                database_df.to_pickle("./database_df.pkl" )

def failure():
    caching.clear_cache()
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
    caching.clear_cache()
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


def PBSxFBS():
    caching.clear_cache()
    #get sheet id FBS vs PBS
    sheet_id='1LxRNFA0LpHjgBrw0HhmfB6w5gpNlsIdbt7L0FzaPFEU'
    #convert google sheet to csv for easy handling
    csv_url=(f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv")
    #create dataframe from csv
    pfbs_df=pd.read_csv(csv_url,on_bad_lines='skip')
    ##################
        
    PBS_file = st.file_uploader("Upload a CSV or Excel file of the Product Breakdown Structure dataset:", type=["csv", "xlsx"])
    if PBS_file is not None:
        PBS = pd.read_csv(PBS_file) if PBS_file.type=='csv' else pd.read_excel(PBS_file)
    else:
        st.warning("Please upload a CSV or Excel file of the Product Breakdown dataset")
    st.markdown("------")
    FBS_file = st.file_uploader("Upload a CSV or Excel file of the Function Breakdown Structure dataset:", type=["csv", "xlsx"])
    if FBS_file is not None:
        FBS = pd.read_csv(FBS_file) if FBS_file.type=='csv' else pd.read_excel(FBS_file)
    else:
        st.warning("Please upload a CSV or Excel file of the Function Breakdown dataset")
    st.markdown("------")
    if st.button("Associate Datasets") and PBS_file is not None and FBS_file is not None:
        pfbs_df = pfbs_df[pfbs_df['1 FBS'].isin(FBS['level 1 Function'].unique())]
        pfbs_df = pfbs_df[pfbs_df['level 2'].isin(FBS['level 2'].unique())]
        pfbs_df = pfbs_df[pfbs_df['MPG name'].isin(PBS['MPG name'].unique())]
        pfbs_df = pfbs_df[pfbs_df['SPG name'].isin(PBS['SPG name'].unique())]

        
        st.dataframe(pfbs_df[['1 FBS','2-3 FBS','MPG name','SPG name']])
        
        
page_names_to_funcs = {
    "Product Breakdown Structure": system_requirement,
    "Material Code":Matcod,
    "Initial FMECA":FMECA,
    "Failure Rate Calculator":failure,
    "Function Breakdown Structure":FBS,
    "Functions and Products Association":PBSxFBS,
    "Standards finder":Standards,
    "Possible Supplier":Supplier,

   
    
    }

selected_page = st.sidebar.radio("Select a page", page_names_to_funcs.keys())
page_names_to_funcs[selected_page]()
