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
        #response = joblib.load(content)
    
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

page_names_to_funcs = {
    "Product Breakdown Structure": system_requirement,
    "Initial FMECA":FMECA,
    "Failure Rate Calculator":failure,
    "Standards finder":Standards,
    "Possible Supplier":Supplier,
    
    }

selected_page = st.sidebar.radio("Select a page", page_names_to_funcs.keys())
page_names_to_funcs[selected_page]()
