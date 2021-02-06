# Copyright (c) 2019 Ultimaker B.V.
# The PostProcessingPlugin is released under the terms of the AGPLv3 or higher.

import math
import re

from ..Script import Script

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
class RetractBeforeWipe(Script):
    def getSettingDataString(self):
        return """{
            "name": "Retract Before Wipe",
            "key": "RetractBeforeWipe",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "comment_retractions":
                {
                    "label": "Comment Retractions",
                    "description": "Add a GCODE comment on retraction lines.",
                    "type": "bool",
                    "default_value": true
                },
                "comment_moves":
                {
                    "label": "Comment Travel Only Moves",
                    "description": "Add a GCODE comment on travel moves without extrusion.",
                    "type": "bool",
                    "default_value": false
                }
            }
        }"""

    def execute(self, data):

        comment_retractions = self.getSettingValueByKey("comment_retractions")
        comment_moves = self.getSettingValueByKey("comment_moves")

        extrusionMatch = re.compile("\AG[01].*(E[\d\-\.]+)")

        for layer_number, layer in enumerate(data):

            lines = layer.split("\n")

            extrusion = 0

            for line_number, line in enumerate(lines):

                extrusionSearch = extrusionMatch.match(line)
                if extrusionSearch:
                    thisExtrusion = extrusionSearch.group(1).replace("E", "")
                else:
                    thisExtrusion = extrusion

                thisExtrusion = float(thisExtrusion)
                    
                if thisExtrusion < extrusion and ( re.findall("\AG[01]\s+F\d+\s+E[\d\-\.]+\Z", line) or re.findall("\AG[01]\s+E[\d\-\.]+\s+F\d+\Z", line) ):
                    lines[line_number] += " ; RETRACTION"

                if re.findall("\AG[01]", line) and not re.findall("E[\d\-\.]+", line):
                    lines[line_number] += " ; NON EXTRUSION MOVE"

                extrusion = thisExtrusion

            for i in range(len(lines)-1, 1, -1):
                if re.findall(" ; RETRACTION", lines[i]):
                    if re.findall(" ; NON EXTRUSION MOVE", lines[i-1]) or re.findall("\A;", lines[i-1]):
                        lines[i], lines[i-1] = lines[i-1], lines[i]
            
            for line_number, line in enumerate(lines):
                if not comment_retractions:
                    lines[line_number] = lines[line_number].replace(" ; RETRACTION", "")
                if not comment_moves:
                    lines[line_number] = lines[line_number].replace(" ; NON EXTRUSION MOVE", "")

            new_layer = "\n".join(lines)

            data[layer_number] = new_layer

        return data
