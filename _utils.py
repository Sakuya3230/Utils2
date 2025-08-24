# -*- coding: utf-8 -*-

import maya.cmds as cmds
import maya.mel as mel
import maya.OpenMaya as om
import maya.api.OpenMaya as om2
import maya.api.OpenMayaAnim as oma2
import maya.api.OpenMayaUI as omui2


ATRRIBUTE_TYPES = [
    om2.MFn.kAttribute2Double,
    om2.MFn.kAttribute2Float,
    om2.MFn.kAttribute2Int,
    om2.MFn.kAttribute2Short,
    om2.MFn.kAttribute3Double,
    om2.MFn.kAttribute3Float,
    om2.MFn.kAttribute3Int,
    om2.MFn.kAttribute3Short,
    om2.MFn.kAttribute4Double,
    om2.MFn.kCompoundAttribute,
    om2.MFn.kDoubleAngleAttribute,
    om2.MFn.kDoubleLinearAttribute,
    om2.MFn.kEnumAttribute,
    om2.MFn.kFloatAngleAttribute,
    om2.MFn.kFloatLinearAttribute,
    om2.MFn.kFloatMatrixAttribute,
    om2.MFn.kGenericAttribute,
    om2.MFn.kLightDataAttribute,
    om2.MFn.kMatrixAttribute,
    om2.MFn.kMessageAttribute,
    om2.MFn.kNumericAttribute,
    om2.MFn.kTimeAttribute,
    om2.MFn.kTypedAttribute,
    om2.MFn.kUnitAttribute 
]

# transform
{'kNumericAttribute', 
 'kAttribute3Float', 
 'kEnumAttribute', 
 'kAttribute2Float', 
 'kAttribute4Double', 
 'kMatrixAttribute', 
 'kDoubleLinearAttribute', 
 'kAttribute3Double', 
 'kTypedAttribute', 
 'kCompoundAttribute', 
 'kGenericAttribute', 
 'kMessageAttribute',
 'kDoubleAngleAttribute'}


def get_numeric_attribute(mPlug):
    mObject_attr = mPlug.attribute()
    value = None
    try:
        mFnNumericAttribute = om2.MFnNumericAttribute(mObject_attr)
        
        if mFnNumericAttribute.numericType() == om2.MFnNumericData.kBoolean: #1
            # print(mPlug.asBool(), "kBoolean")
            value = mPlug.asBool()
            
        elif mFnNumericAttribute.numericType() == om2.MFnNumericData.kByte: #2
            # print(mPlug.asInt(), "kByte")
            value = mPlug.asInt()
            
        elif mFnNumericAttribute.numericType() == om2.MFnNumericData.kShort: #4
            # print(mPlug.asShort(), "kShort")
            value = mPlug.asShort()
            
        elif mFnNumericAttribute.numericType() == om2.MFnNumericData.kLong: #7
            # print(mPlug.asInt(), "kLong")
            value = mPlug.asInt()
            
        elif mFnNumericAttribute.numericType() == om2.MFnNumericData.kFloat: #11
            # print(mPlug.asFloat(), "kFloat")
            value = mPlug.asFloat()
            
        elif mFnNumericAttribute.numericType() == om2.MFnNumericData.k3Float: #13
            # print(get_attribute_3float(mPlug), "k3Float")
            value = get_attribute_3float(mPlug)
            
        elif mFnNumericAttribute.numericType() == om2.MFnNumericData.kDouble: #14
            # print(mPlug.asDouble(), "kDouble")
            value = mPlug.asDouble()
            
        elif mFnNumericAttribute.numericType() == om2.MFnNumericData.k3Double: #16
            # print(get_attribute_3double(mPlug), "k3Double")
            value = get_attribute_3double(mPlug)
            
        else:
            print(u"MFnNumericAttribute無効な値:", mFnNumericAttribute.numericType())
            
    except Exception as e:
        print(e)
        
    return value

def get_component_list(mPlug):
    value = None
    mFnComponentListData = om2.MFnComponentListData(mPlug.asMObject())
    for i in range(mFnComponentListData.length()):
        comp = mFnComponentListData.get(i)
        if comp.hasFn(om2.MFn.kSingleIndexedComponent):
            mFnSingleIndexedComponent = om2.MFnSingleIndexedComponent(comp)
            # print(mFnSingleIndexedComponent.getElements(), "kComponentList")
            value = mFnSingleIndexedComponent.getElements()
            
        elif comp.hasFn(om2.MFn.kDoubleIndexedComponent):
            mFnDoubleIndexedComponent = om2.MFnDoubleIndexedComponent(comp)
            # print(mFnDoubleIndexedComponent.getElements(), "kComponentList")
            value = mFnDoubleIndexedComponent.getElements()
            
        else:
            print("Other", comp.apiTypeStr)
                
    return value

def get_typed_Attribute(mPlug):
    mObject_attr = mPlug.attribute()
    value = None
    try:
        mFnTypedAttribute = om2.MFnTypedAttribute(mObject_attr)
        
        if mFnTypedAttribute.attrType() == om2.MFnData.kInvalid: #0
            # print("kInvalid")
            value = None
        
        elif mFnTypedAttribute.attrType() == om2.MFnData.kString: #4
            print(mPlug.asString(), "kString")
            value = mPlug.asString()
            
        elif mFnTypedAttribute.attrType() == om2.MFnData.kMatrix: #5
            mFnMatrixData = om2.MFnMatrixData(mPlug.asMObject())
            # print(mFnMatrixData.matrix(), "kMatrix")
            value = mFnMatrixData.matrix()
            
        elif mFnTypedAttribute.attrType() == om2.MFnData.kIntArray: #9
            mFnIntArrayData = om2.MFnIntArrayData(mPlug.asMObject())
            # print(mFnIntArrayData.array(), "kIntArray")
            value = mFnIntArrayData.array()
            
        elif mFnTypedAttribute.attrType() == om2.MFnData.kComponentList: #13
            value = get_component_list(mPlug)
            
        elif mFnTypedAttribute.attrType() == om2.MFnData.kMesh: #14
            value = mPlug.asMObject()
                    
        elif mFnTypedAttribute.attrType() == om2.MFnData.kAny: #24
            print("kAny")
            
        else:
            print(u"MFnTypedAttribute無効な値: ", mFnTypedAttribute.attrType())
            
    except Exception as e:
        print(e)

    return value

def get_enum_attribute(mPlug):
    mObject_attr = mPlug.attribute()
    value = None
    try:
        value_index = mPlug.asInt()
        mFnEnumAttribute = om2.MFnEnumAttribute(mObject_attr)
        value_name = mFnEnumAttribute.fieldName(value_index)
        # print(value, value_name, "kEnumAttribute")
        value = [value_index, value_name]
    except Exception as e:
        print(e)

    return value

def get_attribute_num_float(mPlug):
    values = {}
    for i in range(mPlug.numChildren()):
        mPlug_child = mPlug.child(i)
        values[mPlug_child.partialName(useLongNames=True)] = mPlug_child.asFloat()
        
    return values

def get_attribute_num_double(mPlug):
    values = {}
    for i in range(mPlug.numChildren()):
        mPlug_child = mPlug.child(i)
        values[mPlug_child.partialName(useLongNames=True)] = mPlug_child.asDouble()
        
    return values

def get_compound_attribute(mPlug):
    values = {}
    for i in range(mPlug.numChildren()):
        mPlug_child = mPlug.child(i)
        mObject_child = mPlug_child.attribute()
        
        if mPlug_child.isArray:
            values[mPlug_child.partialName(useLongNames=True)] = get_array_attribute(mPlug_child)
        
        elif mObject_child.hasFn(om2.MFn.kCompoundAttribute):
            values[mPlug_child.partialName(useLongNames=True)] = get_compound_attribute(mPlug_child)
        
        elif mObject_child.hasFn(om2.MFn.kNumericAttribute):
           values[mPlug_child.partialName(useLongNames=True)] = get_numeric_attribute(mPlug_child)
            
        elif mObject_child.hasFn(om2.MFn.kEnumAttribute):
            values[mPlug_child.partialName(useLongNames=True)] = get_enum_attribute(mPlug_child)
            
        elif mObject_child.apiType() == om2.MFn.kDoubleLinearAttribute:
            values[mPlug_child.partialName(useLongNames=True)] = mPlug_child.asMDistance()
            
        else:
            print(mPlug_child.partialName(useLongNames=True), mObject_child.apiTypeStr)
            
    return values
    
def get_array_attribute(mPlug):
    values = {}
    if not mPlug.numConnectedElements():
        return None
        
    for i in range(mPlug.numElements()):
        elem_plug = mPlug.elementByPhysicalIndex(i)
        mObject_elem = elem_plug.attribute()
        print(mObject_elem.apiTypeStr)
        
    return values


sl = om2.MGlobal.getSelectionListByName("skinCluster1")
mObject = sl.getDependNode(0)
mFnDependencyNode = om2.MFnDependencyNode(mObject)

try:
    mFnDagNode = om2.MFnDagNode(mObject)
    mDagPath = mFnDagNode.getPath()
except RuntimeError:
    fnDagNode = None
    mDagPath = None
    
print(mFnDependencyNode.name())
attribute_count = mFnDependencyNode.attributeCount()
for i in range(attribute_count):
    mObject_attr = mFnDependencyNode.attribute(i)
    mPlug = om2.MPlug(mObject, mObject_attr)
    
    attr_type = mObject_attr.apiType()
    attr_type_str = mObject_attr.apiTypeStr
    mFnAttribute = om2.MFnAttribute(mObject_attr)
    
    # 最上位のアトリビュートを探索
    if not mFnAttribute.parent.isNull():
        continue    

    if mPlug.isArray:
        print(mPlug.info, "isArray")
        if mPlug.info == "skinCluster1.weightList":
            break
        print(mPlug.numElements())
        #if not mPlug.numConnectedElements():
            #continue
        print(mPlug.numElements())
        
        values = {}
        for i in range(mPlug.numElements()):
            elem_plug = mPlug.elementByPhysicalIndex(i)
            mObject_elem = elem_plug.attribute()
            attr_type = mObject_elem.apiType()
            
            if attr_type == om2.MFn.kCompoundAttribute:
                values[elem_plug.partialName(useLongNames=True)] = get_compound_attribute(elem_plug)
                
            elif attr_type == om2.MFn.kNumericAttribute:
                values[elem_plug.partialName(useLongNames=True)] = get_numeric_attribute(elem_plug)
                
            elif attr_type == om2.MFn.kTypedAttribute:
                values[elem_plug.partialName(useLongNames=True)] = get_typed_Attribute(elem_plug)
                
            elif attr_type == om2.MFn.kAttribute3Float:
                values[elem_plug.partialName(useLongNames=True)] = get_attribute_num_float(elem_plug)
                
            else:
                print(elem_plug.info, elem_plug.attribute().apiTypeStr, "-------------------------------")
                
        print(values)
    
    elif attr_type == om2.MFn.kCompoundAttribute:
        print(mPlug.info, "kCompoundAttribute")
        value = get_compound_attribute(mPlug)
        print(value)
            
    elif attr_type == om2.MFn.kEnumAttribute:
        print(mPlug.info, "kEnumAttribute")
        value = get_enum_attribute(mPlug)
        print(value)
    
    elif attr_type == om2.MFn.kNumericAttribute:
        print(mPlug.info, "kNumericAttribute")
        value = get_numeric_attribute(mPlug)
        print(value)
        
    elif attr_type == om2.MFn.kAttribute3Int:
        print(mPlug.info, "kAttribute3Int")
        value = get_numeric_attribute(mPlug)
        print(value)
        
    elif attr_type == om2.MFn.kTypedAttribute:
        print(mPlug.info, "kTypedAttribute")  
        value = get_typed_Attribute(mPlug)     
        print(value)
        
    elif attr_type == om2.MFn.kMatrixAttribute:
        print(mPlug.info, "kMatrixAttribute")  
        value = get_typed_Attribute(mPlug)     
        print(value)
        
    elif attr_type == om2.MFn.kAttribute2Float:
        print(mPlug.info, "kAttribute2Float")  
        value = get_attribute_num_float(mPlug)
        print(value)
        
    elif attr_type == om2.MFn.kAttribute3Float:
        print(mPlug.info, "kAttribute3Float")  
        value = get_attribute_num_float(mPlug)     
        print(value)
        
    elif attr_type == om2.MFn.kAttribute3Double:
        print(mPlug.info, "kAttribute3Double")  
        value = get_attribute_num_double(mPlug)     
        print(value)
        
    elif attr_type == om2.MFn.kAttribute4Double:
        print(mPlug.info, "kAttribute4Double")
        value = get_attribute_num_double(mPlug)
        print(value)
        
    elif attr_type == om2.MFn.kMessageAttribute:
        print(mPlug.info, "kMessageAttribute")  
        value = None     
        print(value)
       
    elif attr_type == om2.MFn.kGenericAttribute:
        print(mPlug.info, "kGenericAttribute")
        value = None
        print(value)

    elif attr_type == om2.MFn.kOpaqueAttribute:
        print(mPlug.info, "kOpaqueAttribute")
        value = None
        print(value)

    else:
        print(mPlug.info, attr_type_str, attr_type, "---------------------------------------") 


        
        
        
        
        
        
        
        




        
    
# mFnDependencyNode.getAliasList()
# mFnDependencyNode.getConnections()
# mFnDependencyNode.typeId
# mFnDependencyNode.pluginName
# mFnDependencyNode.name()