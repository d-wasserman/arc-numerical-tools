# Name: CreateClassGroupField.py
# Purpose: Will group selected fields into a unique group field for every unique combination of the selected fields.
# Author: David Wasserman
# Last Modified: 3/27/2016
# Copyright: David Wasserman
# Python Version:   2.7-3.1
# ArcGIS Version: 10.3.1 (Pro)
# --------------------------------
# Copyright 2016 David J. Wasserman
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# --------------------------------
# Import Modules
import os, arcpy, datetime
import numpy as np
import itertools

# Define Inputs
FeatureClass = arcpy.GetParameterAsText(0)  # r"C:"
InputFields = arcpy.GetParameterAsText(1)  # "CBSA_POP;D5cri"
BaseName = arcpy.GetParameterAsText(2)  # "GROUP"


# Function Definitions
def funcReport(function=None, reportBool=False):
    """This decorator function is designed to be used as a wrapper with other functions to enable basic try and except
     reporting (if function fails it will report the name of the function that failed and its arguments. If a report
      boolean is true the function will report inputs and outputs of a function.-David Wasserman"""

    def funcReport_Decorator(function):
        def funcWrapper(*args, **kwargs):
            try:
                funcResult = function(*args, **kwargs)
                if reportBool:
                    print("Function:{0}".format(str(function.__name__)))
                    print("     Input(s):{0}".format(str(args)))
                    print("     Ouput(s):{0}".format(str(funcResult)))
                return funcResult
            except Exception as e:
                print(
                    "{0} - function failed -|- Function arguments were:{1}.".format(str(function.__name__), str(args)))
                print(e.args[0])

        return funcWrapper

    if not function:  # User passed in a bool argument
        def waiting_for_function(function):
            return funcReport_Decorator(function)

        return waiting_for_function
    else:
        return funcReport_Decorator(function)


def functionTime(function=None, reportTime=True):
    """ If a report time boolean is true, it will print the datetime before and after function run. Includes
    import with a rare namespace.-David Wasserman"""

    def funcReport_Decorator(function):
        def funcWrapper(*args, **kwargs):
            if reportTime:
                try:
                    # from datetime import datetime as functionDateTime_nsx978 #Optional, but removed
                    print("{0} Function Start:{1}".format(str(function.__name__), str(datetime.datetime.now())))
                except:
                    pass
            funcResult = function(*args, **kwargs)
            if reportTime:
                try:
                    print("{0} Function End:{1}".format(str(function.__name__), str(datetime.datetime.now())))
                except:
                    pass
            return funcResult

        return funcWrapper

    if not function:  # User passed in a bool argument
        def waiting_for_function(function):
            return funcReport_Decorator(function)

        return waiting_for_function
    else:
        return funcReport_Decorator(function)


def arcToolReport(function=None, arcToolMessageBool=False, arcProgressorBool=False):
    """This decorator function is designed to be used as a wrapper with other GIS functions to enable basic try and except
     reporting (if function fails it will report the name of the function that failed and its arguments. If a report
      boolean is true the function will report inputs and outputs of a function.-David Wasserman"""

    def arcToolReport_Decorator(function):
        def funcWrapper(*args, **kwargs):
            try:
                funcResult = function(*args, **kwargs)
                if arcToolMessageBool:
                    arcpy.AddMessage("Function:{0}".format(str(function.__name__)))
                    arcpy.AddMessage("     Input(s):{0}".format(str(args)))
                    arcpy.AddMessage("     Ouput(s):{0}".format(str(funcResult)))
                if arcProgressorBool:
                    arcpy.SetProgressorLabel("Function:{0}".format(str(function.__name__)))
                    arcpy.SetProgressorLabel("     Input(s):{0}".format(str(args)))
                    arcpy.SetProgressorLabel("     Ouput(s):{0}".format(str(funcResult)))
                return funcResult
            except Exception as e:
                arcpy.AddMessage(
                        "{0} - function failed -|- Function arguments were:{1}.".format(str(function.__name__),
                                                                                        str(args)))
                print(
                    "{0} - function failed -|- Function arguments were:{1}.".format(str(function.__name__), str(args)))
                print(e.args[0])

        return funcWrapper

    if not function:  # User passed in a bool argument
        def waiting_for_function(function):
            return arcToolReport_Decorator(function)

        return waiting_for_function
    else:
        return arcToolReport_Decorator(function)


def arcPrint(string, progressor_Bool=False):
    try:
        if progressor_Bool:
            arcpy.SetProgressorLabel(string)
            arcpy.AddMessage(string)
            print(string)
        else:
            arcpy.AddMessage(string)
            print(string)
    except arcpy.ExecuteError:
        arcpy.GetMessages(2)
        pass
    except:
        arcpy.AddMessage("Could not create message, bad arguments.")
        pass


@arcToolReport()
def FieldExist(featureclass, fieldname):
    """ArcFunction
     Check if a field in a feature class field exists and return true it does, false if not.- David Wasserman"""
    fieldList = arcpy.ListFields(featureclass, fieldname)
    fieldCount = len(fieldList)
    if (fieldCount >= 1):  # If there is one or more of this field return true
        return True
    else:
        return False


@arcToolReport()
def AddNewField(in_table, field_name, field_type, field_precision="#", field_scale="#", field_length="#",
                field_alias="#", field_is_nullable="#", field_is_required="#", field_domain="#"):
    """ArcFunction
    Add a new field if it currently does not exist. Add field alone is slower than checking first.- David Wasserman"""
    if FieldExist(in_table, field_name):
        print(field_name + " Exists")
        arcpy.AddMessage(field_name + " Exists")
    else:
        print("Adding " + field_name)
        arcpy.AddMessage("Adding " + field_name)
        arcpy.AddField_management(in_table, field_name, field_type, field_precision, field_scale,
                                  field_length,
                                  field_alias,
                                  field_is_nullable, field_is_required, field_domain)


@arcToolReport
def arc_unique_values(table, field, filter_falsy=False):
    """This function will return a list of unique values from a passed field. If the optional bool is true,
    this function will scrub out null/falsy values. """
    with arcpy.da.SearchCursor(table, [field]) as cursor:
        if filter_falsy:
            return sorted({row[0] for row in cursor if row[0]})
        else:
            return sorted({row[0] for row in cursor})


@arcToolReport
def arc_unique_value_lists(in_feature_class, field_list, filter_falsy=False):
    """Function will returned a nested list of unique values for each field in the same order as the field list."""
    ordered_list = []
    len_list=[]
    for field in field_list:
        unique_vals = arc_unique_values(in_feature_class, field, filter_falsy)
        len_list.append((len(unique_vals)))
        ordered_list.append(unique_vals)
    return ordered_list,len_list


@arcToolReport
def constructSQLEqualityQuery(fieldName, value, dataSource, equalityOperator="="):
    """Creates a workspace sensitive equality query to be used in arcpy/SQL statements. If the value is a string,
    quotes will be used for the query, otherwise they will be removed. Python 2-3 try except catch.(BaseString not in 3)
    David Wasserman"""
    try:  # Python 2
        if isinstance(value, (basestring, str)):
            return "{0} {1} '{2}'".format(arcpy.AddFieldDelimiters(dataSource, fieldName), equalityOperator, str(value))
        else:
            return "{0} {1} {2}".format(arcpy.AddFieldDelimiters(dataSource, fieldName), equalityOperator, str(value))
    except:  # Python 3
        if isinstance(value, (str)):  # Unicode only
            return "{0} {1} '{2}'".format(arcpy.AddFieldDelimiters(dataSource, fieldName), equalityOperator, str(value))
        else:
            return "{0} {1} {2}".format(arcpy.AddFieldDelimiters(dataSource, fieldName), equalityOperator, str(value))


@arcToolReport
def constructChainedSQLQuery(fieldNames, values, dataSource, chainOperator="AND", equalityOperator="="):
    """Creates a workspace sensitive equality query that is chained with some intermediary operator. The function
     will strip the last operator added. The passed fieldNames and values are both assumed to be ordered.
     David Wasserman"""
    fieldNamesLength, valuesLength = len(fieldNames), len(values)
    index_range = range(min(fieldNamesLength, valuesLength))
    final_chained_query = ""
    if fieldNamesLength != valuesLength:
        error_pot_string = "WARNING:Construct Chained SQL Query value/fields lengths do not match. Used minimum. QAQC"
        print(error_pot_string)
        arcpy.AddMessage(error_pot_string)
        arcpy.AddWarning(error_pot_string)
    for idx in index_range:
        base_query = constructSQLEqualityQuery(fieldNames[idx], values[idx], dataSource, equalityOperator)
        final_chained_query = "{0} {1} {2}".format(final_chained_query, chainOperator.strip(), base_query)
    final_chained_query = final_chained_query.strip(" {0} ".format(chainOperator))
    return final_chained_query



@functionTime(reportTime=False)
def create_Class_Group_Field(in_fc, input_Fields, basename="GROUP_"):
    """ This function will take in an feature class, and use pandas/numpy to calculate Z-scores and then
    join them back to the feature class using arcpy."""
    try:
        arcpy.env.overwriteOutput = True
        workspace = os.path.dirname(in_fc)
        OIDFieldName = arcpy.Describe(in_fc).OIDFieldName
        input_Fields_List = input_Fields.split(';')
        arcPrint("Adding Class Fields.", True)
        valid_num_field = arcpy.ValidateFieldName("{0}_Num".format(basename), workspace)
        valid_text_field = arcpy.ValidateFieldName("{0}_Text".format(basename), workspace)
        AddNewField(in_fc, valid_num_field, "LONG")
        AddNewField(in_fc, valid_text_field, "TEXT")
        arcPrint("Computing unique values for input fields.", True)
        nested_unique_values,unique_values_count = arc_unique_value_lists(in_fc, input_Fields_List)
        arcPrint("Generating a combinatorial product.", True)
        field_unique_combos = itertools.product(*nested_unique_values)
        combination_length=np.product(unique_values_count)
        arcPrint("The number of combinations to be tested is : {0}".format(combination_length))
        if combination_length > 1000:
            arcpy.AddWarning(
                "The number of combinations to be tested is over 1 thousand. Memory usage and run time could be large.")
        if combination_length > 10000:
            arcpy.AddWarning(
            "The number of combinations to be tested is over 10 thousand. Memory usage and run time could be very large.")
        if combination_length > 1000000:
            arcpy.AddWarning(
                "The number of combinations to be tested is over 1 million. Memory usage and run time could be huge.")
        if combination_length > 1000000000:
            arcpy.AddWarning(
                "The number of combinations to be tested is over 1 billion. ...What are you doing exactly?")
        counter = 1
        arcPrint("Constructing class groups.", True)
        for combination in field_unique_combos:
            try:
                combination_query = constructChainedSQLQuery(input_Fields_List, combination, in_fc)
                if combination_length<=1000:
                    arcPrint("Processing query: {0}".format(combination_query), True)
                fcNumRecArray = arcpy.da.TableToNumPyArray(in_fc, [OIDFieldName, valid_num_field, valid_text_field],
                                                           where_clause=combination_query,
                                                           null_value={valid_num_field: 0,
                                                                       valid_text_field: "No Data"})
                class_num_array = fcNumRecArray[valid_num_field]
                class_num_array.fill(counter)
                class_string_array = fcNumRecArray[valid_text_field]
                class_string_array.fill(combination_query)
                arcpy.da.ExtendTable(in_fc, OIDFieldName, fcNumRecArray, OIDFieldName, append_only=False)
                counter += 1
            except Exception as e:
                arcPrint("ERROR: Skipped query {0}. QAQC.".format(combination_query), True)
                arcPrint(str(e.args[0]))
        arcPrint("Script Completed Successfully.", True)

    except arcpy.ExecuteError:
        print(arcpy.GetMessages(2))
    except Exception as e:
        print(e.args[0])

        # End do_analysis function


# This test allows the script to be used from the operating
# system command prompt (stand-alone), in a Python IDE,
# as a geoprocessing script tool, or as a module imported in
# another script
if __name__ == '__main__':
    create_Class_Group_Field(FeatureClass, InputFields, BaseName)