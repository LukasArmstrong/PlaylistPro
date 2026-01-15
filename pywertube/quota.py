import datetime as dt

from .logging_config import getLogger
from .database import getDataDB, setDataDB, updateDataDB


def getQuotaUsed(projectID):
    """Get the API quota used for today."""
    gLogger = getLogger()
    gLogger.debug("Entering...")
    optionString = "Where(projectID= " + str(projectID) + ")"
    gLogger.debug(f"Where statement: {optionString}")
    gLogger.debug("Getting Latest date...")
    dbDate = getDataDB('QuotaLimit', ['MAX(date)'], optionString)[0][0]
    gLogger.debug("Latest date obtained!")
    gLogger.debug("Perfroming logic if date is today or not...")
    if dt.date.today() == dbDate:
        gLogger.debug("Date is today...")
        optionString = f"Where Date = \"{dt.date.today().strftime('%Y-%m-%d')}\" and projectID = {projectID}"
        gLogger.debug(f"Where statement: {optionString}")
        gLogger.debug("Getting used quota...")
        amount = getDataDB('QuotaLimit', ['Amount'], optionString)[0][0]
        gLogger.debug("Returning used quota and date...")
        return amount, True
    else:
        gLogger.debug("Date is not today...")
        gLogger.debug("Reseting quota...")
        return 0, False


def setQuotaUsed(inDB, quota, projectID):
    """Store the API quota used for today."""
    gLogger = getLogger()
    gLogger.debug("Entering...")
    if not inDB:
        gLogger.debug("Creating new quota record...")
        setDataDB('QuotaLimit', ['date', 'amount', 'projectID'], [dt.date.today().strftime("%Y-%m-%d"), quota, projectID])
    else:
        gLogger.debug("Updating quota record...")
        optionsString = f"Where Date = \"{dt.date.today().strftime('%Y-%m-%d')}\" and projectID = {projectID}"
        updateDataDB('QuotaLimit', ['Amount'], [quota], optionsString)
    gLogger.debug("Quota Set!")
    gLogger.debug("Leaving...")
