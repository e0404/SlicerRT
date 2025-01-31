import os
import numpy as np
import slicer
import SimpleITK as sitk
import sitkUtils

def prepareCt(beamNode):
    from pyRadPlan.ct import create_ct
    parentPlanNode = beamNode.GetParentPlanNode()
    referenceVolumeNode = parentPlanNode.GetReferenceVolumeNode()
    image = sitkUtils.PullVolumeFromSlicer(referenceVolumeNode)
    return create_ct(cube_hu=image)


def prepareCst(beamNode, ct):
    from pyRadPlan.cst import StructureSet, validate_cst, create_voi
    parentPlanNode = beamNode.GetParentPlanNode()
    referenceVolumeNode = parentPlanNode.GetReferenceVolumeNode()
    node = parentPlanNode.GetSegmentationNode()
    segNode = node.GetSegmentation()
    vois = []
    for id in segNode.GetSegmentIDs():
        segmentArray = slicer.util.arrayFromSegmentBinaryLabelmap(node, id, referenceVolumeNode)
        segmentArray = np.uint8(segmentArray)
        segmentName = segNode.GetSegment(id).GetName()
        voi_type = 'TARGET' if id==parentPlanNode.GetTargetSegmentID() else 'OAR'
        voi = create_voi(voi_type=voi_type, name=segmentName, ct_image=ct, mask=segmentArray)
        vois.append(voi)
    cst = StructureSet(vois=vois, ct_image=ct)
    return cst


def preparePln(beamNode, ct):
    from pyRadPlan.plan import IonPlan, create_pln
    
    ##################### temp #####################
    dose_grid = ct.grid
    dose_grid.resolution = {"x": 5, "y": 5, "z": 5}
    ##################### temp #####################

    '''
    All values in the pln dictionary need to be floats. INCLUDING the numOfFractions.
    '''
    parentPlanNode = beamNode.GetParentPlanNode()
    referenceVolumeNode = parentPlanNode.GetReferenceVolumeNode()

    origin=referenceVolumeNode.GetOrigin()
    ijkToRASDirections = np.eye(3)
    referenceVolumeNode.GetIJKToRASDirections(ijkToRASDirections)
    origin = ijkToRASDirections @ origin

    isocenter = [0]*3
    parentPlanNode.GetIsocenterPosition(isocenter)
    isocenter = ijkToRASDirections @ np.array(isocenter) - np.array(origin)#  + np.array(referenceVolumeNode.GetSpacing())/2.0

    pln = {
        "radiation_mode": ['photons','protons','carbon'][slicer.pyRadPlanEngine.scriptedEngine.integerParameter(beamNode, 'radiationMode')],
        "machine": ['Generic'][slicer.pyRadPlanEngine.scriptedEngine.integerParameter(beamNode, 'machine')],
        # "num_of_fractions": slicer.pyRadPlanEngine.scriptedEngine.doubleParameter(beamNode, 'numOfFractions'),
        "prop_stf": {
            # beam geometry settings
            "bixel_width": 5.0,
            "gantry_angles": [beamNode.GetGantryAngle()],
            "couch_angles": [beamNode.GetCouchAngle()],
            "iso_center": isocenter
        },

        # dose calculation settings
        "prop_dose_calc": {"dose_grid": dose_grid}#ct.grid}

        # # optimization settings
        # "prop_opt": {"optimizer": 'IPOPT',
        #             "bio_optimization": 'none',
        #             "run_dAO": False,
        #             "run_sequencing": True
        #             },
    }
    return create_pln(pln)




