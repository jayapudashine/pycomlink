#----------------------------------------------------------------------------
# Name:         io
# Purpose:      Input and output functions for commercial MW link (CML) data
#
# Authors:      Christian Chwala, Felix Keis
#
# Created:      01.12.2014
# Copyright:    (c) Christian Chwala 2014
# Licence:      The MIT License
#----------------------------------------------------------------------------


from datetime import datetime
import pandas as pd

import psycopg2
import sqlalchemy

from comlink import Comlink


def get_cml_data_from_IFU_database(cml_id, 
                                   t1_str, 
                                   t2_str,
                                   t_str_format='%Y-%m-%d',
                                   db_ip='172.27.60.177', 
                                   db_port='5432',
                                   db_user='MW_parser',
                                   db_password='*MW_parser',
                                   db_name='MW_link'):
    """Query CML data from a database
    
    Parameters
    ----------

    cml_id : str
        ID of the desired CML, e.g. 'MY4320_2_MY2291_4'.
    t1_str : str
        Start time of the desired date range of the data. The standard
        format is '%Y-%m-%d', e.g. '2014-10-30'. Different formats can
        be supplied as 't_str_format'.
    t2_str : str
        Same as 't1_str' but for the end of the date range
    t_str_format : str, optional
        Format string for 't1_str' and 't2_str' according to strptime
        format codes
    db_ip : str, optional
        IP address of database server.
    db_port : str, optional
        Database server port.
    db_user : str, optional
        Databse user.
    db_password : str, optional
        Database user password.
    db_name : str, optional
        Database name.
    
    Returns
    -------

    cml : Comlink
        Comlink class object provided by pycomlink.comlink    
    
    """

    # Convert time strings to datetime    
    t1 = datetime.strptime(t1_str, t_str_format)
    t2 = datetime.strptime(t2_str, t_str_format)    
    
    # Connect to database
    db_connection = psycopg2.connect(database=db_name,
                                     user=db_user, 
                                     password=db_password, 
                                     host=db_ip, 
                                     port=db_port)

    # Check if table with CML ID exists
    if table_exists(db_connection, cml_id.lower()):
        # Create SQL engine to be used by Pandas
        sql_engine = sqlalchemy.create_engine('postgresql://' + 
                                              db_user + 
                                              ':' + db_password +
                                              '@' + db_ip +
                                              ':' + db_port +
                                              '/' + db_name)
                
        # Query data from database using Pandas
        TXRX_df=pd.read_sql("""(SELECT * from """ + cml_id.lower() + 
                       """ WHERE TIMESTAMP >= '""" + str(t1) + 
                       """'::timestamp AND TIMESTAMP <= '"""
                       + str(t2) + """'::timestamp);""",sql_engine, 
                       index_col='timestamp')
        
        # TODO: Parse metadata
        metadata_dict = None
        
        # Build Comlink object from data and metadata
        cml = Comlink(metadata_dict, TXRX_df)
    else:
        ValueError('Table for MW_link_ID %s does not exists in database' % 
                   cml_id)
    db_connection.close()
    return cml
    
    
def table_exists(con, table_str):
    """Check if a MW_link data table exists in the database
    
    Parameters
    ----------
    
    con : psycopg2.connection
        Database server connection object provided by psycopg2
    tabes_str : str
        String of table name for which the existenst will be checked
        
    Returns
    -------
    
    exists : bool
        True or False, whether the table exists or not
        
    """
    
    exists = False
    try:
        cur = con.cursor()
        cur.execute("select exists(select relname from pg_class where relname='"
                    + table_str + "')")
        exists = cur.fetchone()[0]    
    except psycopg2.Error as e:
         print e  
    return exists