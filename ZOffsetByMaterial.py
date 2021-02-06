# Copyright (c) 2019 Ultimaker B.V.
# The PostProcessingPlugin is released under the terms of the AGPLv3 or higher.

import math
import re

from ..Script import Script
from UM.Application import Application
from UM.Logger import Logger

#Example Settings
#"settings":
#{
#  "extra_retraction_speed":
#  {
#    "label": "Extra Retraction Ratio",
#    "description": "How much does it retract during the travel move, by ratio of the travel length.",
#    "type": "float",
#    "default_value": 0.05
#  }
#}
##  Continues retracting during all travel moves.
class ZOffsetByMaterial(Script):
    def getSettingDataString(self):
        return """{
            "name": "Z Offset By Material",
            "key": "ZOffsetByMaterial",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "pla_offset":
                {
                    "label": "PLA Z Offset",
                    "description": "Additional Z Offset for PLA.",
                    "type": "float",
                    "default_value": 0.0
                },
                "petg_offset":
                {
                    "label": "PETG Z Offset",
                    "description": "Additonal Z Offset for PETG",
                    "type": "float",
                    "default_value": 0.0
                }
            }
        }"""

    def execute(self, data):

        pla_offset = self.getSettingValueByKey("pla_offset")
        petg_offset = self.getSettingValueByKey("petg_offset")

        # add extruder specific data to slice info
        material = Application.getInstance().getGlobalContainerStack().extruderList[0].material.getMetaData().get("material", "")

        adhesion_z_offset = float(Application.getInstance().getGlobalContainerStack().getProperty("adhesion_z_offset", "value"))
        if adhesion_z_offset is None:
            adhesion_z_offset = 0

        layer_height_0 = float(Application.getInstance().getGlobalContainerStack().getProperty("layer_height_0", "value"))

        for layer_number, layer in enumerate(data):

            lines = layer.split("\n")

            for line_number, line in enumerate(lines):

                if re.findall(";LAYER:0", line):

                    if material.lower() == "pla":
                        offset = float(pla_offset)
                    elif material.lower() == "petg":
                        offset = float(petg_offset)

                    Logger.log("i", "Using Material specific Z offset of " + str(offset) + " for " + material)

                    totalOffset = offset + adhesion_z_offset

                    if totalOffset < -1 * layer_height_0:
                        oldOffset = offset
                        offset = layer_height_0 + adhesion_z_offset
                        Logger.log("w", "Total offset (" + material + " Z Offset [" + str(oldOffset) + "] + Fixed Z Offset [" + str(adhesion_z_offset) + "]) was too high.  Setting " + material + " Z Offset to " + str(offset) + ".")

                    if offset < -10:
                        Logger.log("w", "Offset " + str(offset)  + " is less than -10.  Setting offset to minimum value of -10.")
                        offset = -10

                    if offset > 10:
                        Logger.log("w", "Offset " + str(offset) + " is greater than 10.  Setting offset to maximum value of 10.")
                        offset = 10

                    lines.insert(1,"G1 F600 Z" + str(10 - offset) + " ; Adding Z Offset for " + material);
                    lines.insert(2,"G92 Z10.0 ; Adding Z Offset for " + material);

                    break

            new_layer = "\n".join(lines)

            data[layer_number] = new_layer

        return data
