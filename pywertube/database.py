import mariadb
from .logging_config import getLogger
from .utils import checkType, sanitizeTitle

# Global database connection
gDBconn = None


def getDataBaseConnection(usr, pswd, host, port, db):
    """Establish a connection to the MariaDB database."""
    gLogger = getLogger()
    gLogger.debug("Entering...")
    gLogger.debug("Checking types...")
    checkType(usr, str)
    checkType(pswd, str)
    checkType(host, str)
    checkType(port, int)
    checkType(db, str)
    try:
        gLogger.debug("Attempting MariaDB connection...")
        global gDBconn
        gDBconn = mariadb.connect(
            user=usr,
            password=pswd,
            host=host,
            port=port,
            database=db
        )
        gLogger.debug("Database Connection established!")
    except mariadb.Error as e:
        gLogger.error(f"Error connecting to MariaDB Platform.  Type: {type(e)} Arguements:{e}", usr=usr, pswd=pswd, host=host, port=port, db=db)
        raise mariadb.Error(e)
    gLogger.debug("Leaving...")


def getDataDB(tableString, cols, optionsString=""):
    """Execute a SELECT query and return results."""
    gLogger = getLogger()
    gLogger.debug("Entering...")
    gLogger.debug("Checking types...")
    checkType(tableString, str)
    checkType(cols, list)
    cur = gDBconn.cursor()
    gLogger.debug("Get connection cursor obtained...")
    query = "Select " + " ,".join(cols) + " from " + tableString + " " + optionsString
    try:
        gLogger.debug("Attempting query...")
        cur.execute(query)
        gLogger.debug("Query Successful!")
    except mariadb.Error as e:
        gLogger.error(f"Error executing query {query}.  Type: {type(e)} Arguements:{e}", conn=gDBconn, tableString=tableString, cols=cols)
        raise mariadb.Error(e)
    gLogger.debug("Leaving...")
    return cur.fetchall()


def setDataDB(tableString, cols_list, vals_list, optionsString=""):
    """Execute an INSERT query."""
    gLogger = getLogger()
    gLogger.debug("Entering...")
    gLogger.debug("Checking Number of Columns = Number of values to assign...")
    if len(cols_list) != len(vals_list):
        gLogger.error("Lengths of Columns and Values differ!", DB_Connection=gDBconn, Table=tableString, Columns=cols_list, Values=vals_list)
        raise ValueError("Lengths of Columns and Values differ!")
    gLogger.debug("Checking types...")
    checkType(tableString, str)
    checkType(cols_list, list)
    checkType(vals_list, list)
    checkType(optionsString, str)
    cur = gDBconn.cursor()
    gLogger.debug("Set connection cursor obtained!")
    query = f"Insert Into {tableString}{*cols_list,}"
    query = query.replace("'", "`")
    query += f" Values {*vals_list,} {optionsString}"
    try:
        gLogger.debug("Attempting query...")
        cur.execute(query)
        gLogger.debug("Query Successful!")
        gDBconn.commit()
        gLogger.debug("Query Committed!")
    except mariadb.Error as e:
        gLogger.error(f"Error executing query {query}.  Type: {type(e)} Arguements:{e}", DB_Connection=gDBconn, Table=tableString, Columns=cols_list, Values=vals_list)
        raise mariadb.Error(e)
    gLogger.debug(f"Leaving...")


def updateDataDB(tableString, cols_list, vals_list, optionsString=""):
    """Execute an UPDATE query."""
    gLogger = getLogger()
    gLogger.debug("Entering...")
    gLogger.debug("Checking Number of Columns = Number of values to assign...")
    if len(cols_list) != len(vals_list):
        gLogger.error("Lengths of Columns and Values differ!", DB_Connection=gDBconn, Table=tableString, Columns=cols_list, Values=vals_list)
        raise ValueError("Lengths of Columns and Values differ!")
    gLogger.debug("Checking types...")
    checkType(tableString, str)
    checkType(cols_list, list)
    checkType(vals_list, list)
    checkType(optionsString, str)
    cur = gDBconn.cursor()
    gLogger.debug("Update connection cursor obtained!")
    query = f"Update {tableString} set { ', '.join(f'`{x}` = {str(vals_list[i])}' for i, x in enumerate(cols_list)) } {optionsString}"
    try:
        gLogger.debug("Attempting query...")
        cur.execute(query)
        gLogger.debug("Query Successful!")
        gDBconn.commit()
        gLogger.debug("Query Committed!")
    except mariadb.Error as e:
        gLogger.error(f"Error executing query {query}.  Type: {type(e)} Arguements:{e}", DB_Connection=gDBconn, Table=tableString, Columns=cols_list, Values=vals_list)
        raise mariadb.Error(e)
    gLogger.debug(f"Leaving...")


def clearTableDB(tableString):
    """Delete all records from a table."""
    gLogger = getLogger()
    gLogger.debug("Entering...")
    gLogger.debug("Checking types...")
    checkType(tableString, str)
    cur = gDBconn.cursor()
    gLogger.debug("Delete connection cursor obtained!")
    query = f"Delete From {tableString}"
    try:
        gLogger.debug("Attempting query...")
        cur.execute(query)
        gLogger.debug("Query Successful!")
        gDBconn.commit()
        gLogger.debug("Query Committed!")
    except mariadb.Error as e:
        gLogger.error(f"Error executing query {query}.  Type: {type(e)} Arguements:{e}", DB_Connection=gDBconn, Table=tableString)
        raise mariadb.Error(e)
    gLogger.debug(f"Leaving...")


def storeWatchLaterDB(watchlater):
    """Store the watch later list in the database."""
    gLogger = getLogger()
    gLogger.debug("Entering...")
    gLogger.debug("Checking types...")
    checkType(watchlater, list)
    clearTableDB('WatchLaterList')
    gLogger.debug("WatchLaterList Cleared!")
    gLogger.debug("Filling new list...")
    for video in watchlater:
        videoList = list(video)
        videoList[6] = sanitizeTitle(videoList[6])
        setDataDB('WatchLaterList', ['position', 'playlistID', 'videoID', 'duration', 'creator', 'publishedTimeUTC', 'title'], videoList, 'ON DUPLICATE KEY UPDATE position=Value(position)')
    gLogger.debug("Watch Later stored in database!")
    gLogger.debug(f"Leaving...")


def closeDBConnection():
    """Close the database connection."""
    gLogger = getLogger()
    gLogger.debug("Entering...")
    gLogger.debug("Closing DB connection...")
    global gDBconn
    gDBconn.close()
    gLogger.debug("Clearing Global DB connection variable...")
    gDBconn = None
    gLogger.debug("Cleared! Leaving...")


# Keep old name for backwards compatibility
CloseDBconnnection = closeDBConnection
