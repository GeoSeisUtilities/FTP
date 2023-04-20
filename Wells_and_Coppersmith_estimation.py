"""
Model exported as python.
Name : Wells and Coppersmith estimation
Group : 
With QGIS : 32805
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterField
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsProperty
import processing


class WellsAndCoppersmithEstimation(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('Faults', 'Faults', types=[QgsProcessing.TypeVectorLine], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('Eqs', 'Eqs', types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterField('Depthfieldkm', 'Depth field (km)', type=QgsProcessingParameterField.Numeric, parentLayerParameterName='Eqs', allowMultiple=False, defaultValue=None))
        self.addParameter(QgsProcessingParameterField('Dipangle', 'Dip angle', type=QgsProcessingParameterField.Any, parentLayerParameterName='Faults', allowMultiple=False, defaultValue=None))
        self.addParameter(QgsProcessingParameterField('Dipdirectionfield', 'Dip direction', type=QgsProcessingParameterField.Any, parentLayerParameterName='Faults', allowMultiple=False, defaultValue=None))
        self.addParameter(QgsProcessingParameterField('Kinematic', 'Kinematic', type=QgsProcessingParameterField.String, parentLayerParameterName='Faults', allowMultiple=False, defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('BufferWithEstimatedParameters', 'buffer with estimated parameters', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(49, model_feedback)
        results = {}
        outputs = {}

        # Rinomina campo (Profondità)
        alg_params = {
            'FIELD': parameters['Depthfieldkm'],
            'INPUT': parameters['Eqs'],
            'NEW_NAME': 'D_F_______',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RinominaCampoProfondit'] = processing.run('native:renametablefield', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Rinomina campo (Dip angle)
        alg_params = {
            'FIELD': parameters['Dipangle'],
            'INPUT': parameters['Faults'],
            'NEW_NAME': 'D_A_______',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RinominaCampoDipAngle'] = processing.run('native:renametablefield', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Aggiungi campo autoincrementale
        alg_params = {
            'FIELD_NAME': 'AUTO',
            'GROUP_FIELDS': [''],
            'INPUT': outputs['RinominaCampoDipAngle']['OUTPUT'],
            'SORT_ASCENDING': True,
            'SORT_EXPRESSION': '',
            'SORT_NULLS_FIRST': False,
            'START': 0,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['AggiungiCampoAutoincrementale'] = processing.run('native:addautoincrementalfield', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Rinomina campo (Dip Direction)
        alg_params = {
            'FIELD': parameters['Dipdirectionfield'],
            'INPUT': outputs['AggiungiCampoAutoincrementale']['OUTPUT'],
            'NEW_NAME': 'DIP_DIR',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RinominaCampoDipDirection'] = processing.run('native:renametablefield', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Da parti multiple a parti singole
        alg_params = {
            'INPUT': outputs['RinominaCampoDipDirection']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DaPartiMultipleAPartiSingole'] = processing.run('native:multiparttosingleparts', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Calcolatore di campi (Bearing)
        alg_params = {
            'FIELD_LENGTH': 6,
            'FIELD_NAME': 'BEARING',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0,  # Decimale (doppia precisione)
            'FORMULA': '(atan((xat(-1)-xat(0))/(yat(-1)-yat(0)))) * 180/3.14159 + (180 *(((yat(-1)-yat(0)) < 0) + (((xat(-1)-xat(0)) < 0 AND (yat(-1) - yat(0)) >0)*2)))',
            'INPUT': outputs['DaPartiMultipleAPartiSingole']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalcolatoreDiCampiBearing'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # Calcolatore di campi (Direction) (N)
        alg_params = {
            'FIELD_LENGTH': 3,
            'FIELD_NAME': 'DIRECTION',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # Testo (stringa)
            'FORMULA': 'if ("BEARING" <= 45 OR "BEARING" >315, \'N\', "DIRECTION")',
            'INPUT': outputs['CalcolatoreDiCampiBearing']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalcolatoreDiCampiDirectionN'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # Calcolatore di campi (Direction) (E)
        alg_params = {
            'FIELD_LENGTH': 3,
            'FIELD_NAME': 'DIRECTION',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # Testo (stringa)
            'FORMULA': 'if ("BEARING" > 45 AND "BEARING" <= 135, \'E\', "DIRECTION")',
            'INPUT': outputs['CalcolatoreDiCampiDirectionN']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalcolatoreDiCampiDirectionE'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # Calcolatore di campi (Direction) (S)
        alg_params = {
            'FIELD_LENGTH': 3,
            'FIELD_NAME': 'DIRECTION',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # Testo (stringa)
            'FORMULA': 'if ("BEARING" <= 225 AND "BEARING" >135, \'S\', "DIRECTION")',
            'INPUT': outputs['CalcolatoreDiCampiDirectionE']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalcolatoreDiCampiDirectionS'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # Calcolatore di campi (Direction) (W)
        alg_params = {
            'FIELD_LENGTH': 3,
            'FIELD_NAME': 'DIRECTION',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # Testo (stringa)
            'FORMULA': 'if ("BEARING" <= 315 AND "BEARING" >225, \'W\', "DIRECTION")',
            'INPUT': outputs['CalcolatoreDiCampiDirectionS']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalcolatoreDiCampiDirectionW'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(10)
        if feedback.isCanceled():
            return {}

        # Calcolatore di campi (DIP) (EAST)
        alg_params = {
            'FIELD_LENGTH': 6,
            'FIELD_NAME': 'DipDir',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # Testo (stringa)
            'FORMULA': 'if("DIP_DIR" = \'EST\' OR "DIP_DIR" = \'est\' OR "DIP_DIR" = \'Est\' OR "DIP_DIR" = \'EAST\' OR "DIP_DIR" = \'East\' OR "DIP_DIR" = \'east\' OR "DIP_DIR" = \'E\' OR "DIP_DIR" = \'e\' OR "DIP_DIR" = \'Nord-est\' OR "DIP_DIR" = \'Nord-Est\' OR "DIP_DIR" = \'NORD-EST\' OR "DIP_DIR" = \'nord-est\' OR "DIP_DIR" = \'North-east\' OR "DIP_DIR" = \'North-East\' OR "DIP_DIR" = \'NORTH-EAST\' OR "DIP_DIR" = \'north-east\' OR "DIP_DIR" = \'NE\' OR "DIP_DIR" = \'Ne\' OR "DIP_DIR" = \'ne\' OR "DIP_DIR" = \'Est-Nord-Est\' OR "DIP_DIR" = \'EST-NORD-EST\' OR "DIP_DIR" = \'est-nord-est\' OR "DIP_DIR" = \'Est-nord-est\' OR "DIP_DIR" = "Est-Sud-Est" OR "DIP_DIR" = \'est-sud-est\' OR "DIP_DIR" = \'EST-SUD-EST\' OR "DIP_DIR" = \'Est-sud-est\' OR "DIP_DIR" = \'East-South-East\' OR "DIP_DIR" = \'EAST-SOUTH-EAST\' OR "DIP_DIR" = \'east-south-east\' OR "DIP_DIR" = \'East-south-east\' OR "DIP_DIR" = \'EAST-NORTH-EAST\' OR "DIP_DIR" = \'East-North-East\' OR "DIP_DIR" = \'east-north-east\' OR "DIP_DIR" = \'East-north-east\' OR "DIP_DIR" = \'ENE\' OR "DIP_DIR" = \'ene\' OR "DIP_DIR" = \'Ene\' OR "DIP_DIR" = \'ESE\' OR "DIP_DIR" = \'ese\' OR "DIP_DIR" = \'Ese\', \'EAST\', "DipDir")',
            'INPUT': outputs['CalcolatoreDiCampiDirectionW']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalcolatoreDiCampiDipEast'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(11)
        if feedback.isCanceled():
            return {}

        # Calcolatore di campi (DIP) (NORTH)
        alg_params = {
            'FIELD_LENGTH': 6,
            'FIELD_NAME': 'DipDir',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # Testo (stringa)
            'FORMULA': 'if("DIP_DIR" = \'NORD\' OR "DIP_DIR" = \'nord\' OR "DIP_DIR" = \'Nord\' OR "DIP_DIR" = \'NORTH\' OR "DIP_DIR" = \'North\' OR "DIP_DIR" = \'north\' OR "DIP_DIR" = \'N\' OR "DIP_DIR" = \'n\' OR "DIP_DIR" = \'Nord-est\' OR "DIP_DIR" = \'Nord-Est\' OR "DIP_DIR" = \'NORD-EST\' OR "DIP_DIR" = \'nord-est\' OR "DIP_DIR" = \'North-east\' OR "DIP_DIR" = \'North-East\' OR "DIP_DIR" = \'NORTH-EAST\' OR "DIP_DIR" = \'north-east\' OR "DIP_DIR" = \'NE\' OR "DIP_DIR" = \'Ne\' OR "DIP_DIR" = \'ne\' OR "DIP_DIR" = \'Nord-nord-ovest\' OR "DIP_DIR" = \'NORD-NORD-OVEST\' OR "DIP_DIR" = \'nord-nord-ovest\' OR "DIP_DIR" = \'Nord-Nord-Ovest\' OR "DIP_DIR" = \'Nord-nord-est\' OR "DIP_DIR" = \'nord-nord-est\' OR "DIP_DIR" = \'NORD-NORD-EST\' OR "DIP_DIR" = \'Nord-Nord-Est\' OR "DIP_DIR" = \'North-north-west\' OR "DIP_DIR" = \'NORTH-NORTH-WEST\' OR "DIP_DIR" = \'north-north-west\' OR "DIP_DIR" = \'North-North-West\' OR "DIP_DIR" = \'North-north-east\' OR "DIP_DIR" = \'North-North-East\' OR "DIP_DIR" = \'NORTH-NORTH-EAST\' OR "DIP_DIR" = \'north-north-east\' OR "DIP_DIR" = \'NNW\' OR "DIP_DIR" = \'nnw\' OR "DIP_DIR" = \'Nnw\' OR "DIP_DIR" = \'NNO\' OR "DIP_DIR" = \'nno\' OR "DIP_DIR" = \'Nno\' OR "DIP_DIR" = \'NNE\' OR "DIP_DIR" = \'nne\', \'NORTH\', "DipDir")',
            'INPUT': outputs['CalcolatoreDiCampiDipEast']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalcolatoreDiCampiDipNorth'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(12)
        if feedback.isCanceled():
            return {}

        # Calcolatore di campi (DIP) (SOUTH)
        alg_params = {
            'FIELD_LENGTH': 6,
            'FIELD_NAME': 'DipDir',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # Testo (stringa)
            'FORMULA': 'if("DIP_DIR" = \'SUD\' OR "DIP_DIR" = \'sud\' OR "DIP_DIR" = \'Sud\' OR "DIP_DIR" = \'SOUTH\' OR "DIP_DIR" = \'South\' OR "DIP_DIR" = \'south\' OR "DIP_DIR" = \'S\' OR "DIP_DIR" = \'s\' OR "DIP_DIR" = \'Sud-est\' OR "DIP_DIR" = \'Sud-Est\' OR "DIP_DIR" = \'SUD-EST\' OR "DIP_DIR" = \'sud-est\' OR "DIP_DIR" = \'South-east\' OR "DIP_DIR" = \'South-East\' OR "DIP_DIR" = \'SOUTH-EAST\' OR "DIP_DIR" = \'south-east\' OR "DIP_DIR" = \'SE\' OR "DIP_DIR" = \'Se\' OR "DIP_DIR" = \'se\' OR "DIP_DIR" = \'Sud-Sud-Est\' OR "DIP_DIR" = \'SUD-SUD-EST\' OR "DIP_DIR" = \'sud-sud-est\' OR "DIP_DIR" = \'Sud-sud-est\' OR "DIP_DIR" = \'Sud-Sud-Ovest\' OR "DIP_DIR" = \'sud-sud-ovest\' OR "DIP_DIR" = \'SUD-SUD-OVEST\' OR "DIP_DIR" = \'Sud-sud-ovest\' OR "DIP_DIR" = \'South-South-West\' OR "DIP_DIR" = \'SOUTH-SOUTH-WEST\' OR "DIP_DIR" = \'south-south-west\' OR "DIP_DIR" = \'south-south-west\' OR "DIP_DIR" = \'South-South-East\' OR "DIP_DIR" = \'South-south-east\' OR "DIP_DIR" = \'SOUTH-SOUTH-EAST\' OR "DIP_DIR" = \'south-south-east\' OR "DIP_DIR" = \'SSE\' OR "DIP_DIR" = \'sse\' OR "DIP_DIR" = \'Sse\' OR "DIP_DIR" = \'SSW\' OR "DIP_DIR" = \'ssw\' OR "DIP_DIR" = \'Ssw\' OR "DIP_DIR" = \'SSO\' OR "DIP_DIR" = \'sso\' OR "DIP_DIR" = \'Sso\', \'SOUTH\', "DipDir")',
            'INPUT': outputs['CalcolatoreDiCampiDipNorth']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalcolatoreDiCampiDipSouth'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(13)
        if feedback.isCanceled():
            return {}

        # Calcolatore di campi (DIP) (WEST)
        alg_params = {
            'FIELD_LENGTH': 6,
            'FIELD_NAME': 'DipDir',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # Testo (stringa)
            'FORMULA': 'if("DIP_DIR" = \'OVEST\' OR "DIP_DIR" = \'ovest\' OR "DIP_DIR" = \'Ovest\' OR "DIP_DIR" = \'WEST\' OR "DIP_DIR" = \'West\' OR "DIP_DIR" = \'west\' OR "DIP_DIR" = \'W\' OR "DIP_DIR" = \'w\' OR "DIP_DIR" = \'O\' OR "DIP_DIR" = \'o\' OR "DIP_DIR" = \'Sud-ovest\' OR "DIP_DIR" = \'Sud-Ovest\' OR "DIP_DIR" = \'SUD-OVEST\' OR "DIP_DIR" = \'sud-ovest\' OR "DIP_DIR" = \'South-west\' OR "DIP_DIR" = \'South-West\' OR "DIP_DIR" = \'SOUTH-WEST\' OR "DIP_DIR" = \'south-west\' OR "DIP_DIR" = \'SW\' OR "DIP_DIR" = \'Sw\' OR "DIP_DIR" = \'sw\' OR "DIP_DIR" = \'SO\' OR "DIP_DIR" = \'So\' OR "DIP_DIR" = \'so\' OR "DIP_DIR" = \'Ovest-Sud-Ovest\' OR "DIP_DIR" = \'OVEST-SUD-OVEST\' OR "DIP_DIR" = \'ovest-sud-ovest\' OR "DIP_DIR" = \'Ovest-sud-ovest\' OR "DIP_DIR" = \'Ovest-nord-ovest\' OR "DIP_DIR" = \'ovest-nord-ovest\' OR "DIP_DIR" = \'OVEST-NORD-OVEST\' OR "DIP_DIR" = \'Ovest-Nord-Ovest\' OR "DIP_DIR" = \'West-North-West\' OR "DIP_DIR" = \'WEST-NORTH-WEST\' OR "DIP_DIR" = \'west-north-west\' OR  "DIP_DIR" = \'West-north-west\' OR "DIP_DIR" = \'West-south-west\' OR "DIP_DIR" = \'West-South-West\' OR "DIP_DIR" = \'WEST-SOUTH-WEST\' OR "DIP_DIR" = \'west-south-west\' OR "DIP_DIR" = \'WSW\' OR "DIP_DIR" = \'wsw\' OR "DIP_DIR" = \'Wsw\' OR "DIP_DIR" = \'OSO\' OR "DIP_DIR" = \'oso\' OR "DIP_DIR" = \'Oso\' OR "DIP_DIR" = \'WNW\' OR "DIP_DIR" = \'wnw\' OR "DIP_DIR" = \'Wnw\' OR "DIP_DIR" = \'ONO\' OR "DIP_DIR" = \'ono\' OR "DIP_DIR" = \'Ono\', \'WEST\', "DipDir")',
            'INPUT': outputs['CalcolatoreDiCampiDipSouth']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalcolatoreDiCampiDipWest'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(14)
        if feedback.isCanceled():
            return {}

        # Calcolatore di campi (DIRECTION2) (N-E)
        alg_params = {
            'FIELD_LENGTH': 3,
            'FIELD_NAME': 'DIRECTION2',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # Testo (stringa)
            'FORMULA': 'if ("BEARING" >=0 AND "BEARING" <90, \'N-E\', "DIRECTION2")',
            'INPUT': outputs['CalcolatoreDiCampiDipWest']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalcolatoreDiCampiDirection2Ne'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(15)
        if feedback.isCanceled():
            return {}

        # Calcolatore di campi (DIRECTION2) (S-E)
        alg_params = {
            'FIELD_LENGTH': 3,
            'FIELD_NAME': 'DIRECTION2',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # Testo (stringa)
            'FORMULA': 'if ("BEARING" >=90 AND "BEARING" <180, \'S-E\', "DIRECTION2")',
            'INPUT': outputs['CalcolatoreDiCampiDirection2Ne']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalcolatoreDiCampiDirection2Se'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(16)
        if feedback.isCanceled():
            return {}

        # Calcolatore di campi (DIRECTION2) (S-W)
        alg_params = {
            'FIELD_LENGTH': 3,
            'FIELD_NAME': 'DIRECTION2',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # Testo (stringa)
            'FORMULA': 'if ("BEARING" >=180 AND "BEARING" <270, \'S-W\', "DIRECTION2")',
            'INPUT': outputs['CalcolatoreDiCampiDirection2Se']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalcolatoreDiCampiDirection2Sw'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(17)
        if feedback.isCanceled():
            return {}

        # Calcolatore di campi (DIRECTION2) (N-W)
        alg_params = {
            'FIELD_LENGTH': 3,
            'FIELD_NAME': 'DIRECTION2',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # Testo (stringa)
            'FORMULA': 'if ("BEARING" >=270 AND "BEARING" <360, \'N-W\', "DIRECTION2")',
            'INPUT': outputs['CalcolatoreDiCampiDirection2Sw']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalcolatoreDiCampiDirection2Nw'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(18)
        if feedback.isCanceled():
            return {}

        # Calcolatore di campi (DIP2) (NORTH-EAST)
        alg_params = {
            'FIELD_LENGTH': 15,
            'FIELD_NAME': 'DipDir2',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # Testo (stringa)
            'FORMULA': 'if("DIP_DIR" = \'NORD-EST\' OR "DIP_DIR" = \'nord-est\' OR "DIP_DIR" = \'Nord-est\' OR "DIP_DIR" = \'Nord-Est\' OR "DIP_DIR" = \'north-east\' OR "DIP_DIR" = \'North-east\' OR "DIP_DIR" = \'North-East\' OR "DIP_DIR" = \'NORTH-EAST\' OR "DIP_DIR" = \'ne\' OR "DIP_DIR" = \'Ne\' OR "DIP_DIR" = \'NE\' OR "DIP_DIR" = \'nord-nord-est\' OR "DIP_DIR" = \'Nord-nord-est\' OR "DIP_DIR" = \'Nord-Nord-Est\' OR "DIP_DIR" = \'NORD-NORD-EST\' OR "DIP_DIR" = \'north-north-east\' OR "DIP_DIR" = \'North-north-east\' OR "DIP_DIR" = \'North-North-East\' OR "DIP_DIR" = \'NORTH-NORTH-EAST\' OR "DIP_DIR" = \'nne\' OR "DIP_DIR" = \'Nne\' OR "DIP_DIR" = \'NNE\' OR "DIP_DIR" = \'est-nord-est\' OR "DIP_DIR" = \'Est-nord-est\' OR "DIP_DIR" = \'Est-Nord-Est\' OR "DIP_DIR" = \'EST-NORD-EST\' OR "DIP_DIR" = \'east-north-east\' OR "DIP_DIR" = \'East-north-east\' OR "DIP_DIR" = \'East-North-East\' OR "DIP_DIR" = \'EAST-NORTH-EAST\' OR "DIP_DIR" = \'ene\' OR "DIP_DIR" = \'Ene\' OR "DIP_DIR" = \'ENE\' OR "DIP_DIR" = \'est\' OR "DIP_DIR" = \'Est\' OR "DIP_DIR" = \'EST\' OR "DIP_DIR" = \'east\' OR "DIP_DIR" = \'East\' OR "DIP_DIR" = \'EAST\' OR "DIP_DIR" = \'e\' OR "DIP_DIR" = \'E\', \'NORTH-EAST\', "DipDir2")',
            'INPUT': outputs['CalcolatoreDiCampiDirection2Nw']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalcolatoreDiCampiDip2Northeast'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(19)
        if feedback.isCanceled():
            return {}

        # Calcolatore di campi (DIP2) (SOUTH-EAST)
        alg_params = {
            'FIELD_LENGTH': 15,
            'FIELD_NAME': 'DipDir2',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # Testo (stringa)
            'FORMULA': 'if("DIP_DIR" = \'SUD-EST\' OR "DIP_DIR" = \'sud-est\' OR "DIP_DIR" = \'Sud-est\' OR "DIP_DIR" = \'Sud-Est\' OR "DIP_DIR" = \'south-east\' OR "DIP_DIR" = \'South-east\' OR "DIP_DIR" = \'South-East\' OR "DIP_DIR" = \'SOUTH-EAST\' OR "DIP_DIR" = \'se\' OR "DIP_DIR" = \'Se\' OR "DIP_DIR" = \'SE\' OR "DIP_DIR" = \'sud-sud-est\' OR "DIP_DIR" = \'Sud-sud-est\' OR "DIP_DIR" = \'Sud-Sud-Est\' OR "DIP_DIR" = \'SUD-SUD-EST\' OR "DIP_DIR" = \'south-south-east\' OR "DIP_DIR" = \'South-south-east\' OR "DIP_DIR" = \'South-South-East\' OR "DIP_DIR" = \'SOUTH-SOUTH-EAST\' OR "DIP_DIR" = \'sse\' OR "DIP_DIR" = \'Sse\' OR "DIP_DIR" = \'SSE\' OR "DIP_DIR" = \'est-sud-est\' OR "DIP_DIR" = \'Est-sud-est\' OR "DIP_DIR" = \'Est-Sud-Est\' OR "DIP_DIR" = \'EST-SUD-EST\' OR "DIP_DIR" = \'east-south-east\' OR "DIP_DIR" = \'East-south-east\' OR "DIP_DIR" = \'East-South-East\' OR "DIP_DIR" = \'EAST-SOUTH-EAST\' OR "DIP_DIR" = \'ese\' OR "DIP_DIR" = \'Ese\' OR "DIP_DIR" = \'ESE\' OR "DIP_DIR" = \'sud\' OR "DIP_DIR" = \'Sud\' OR "DIP_DIR" = \'SUD\' OR "DIP_DIR" = \'south\' OR "DIP_DIR" = \'South\' OR "DIP_DIR" = \'SOUTH\' OR "DIP_DIR" = \'s\' OR "DIP_DIR" = \'S\', \'SOUTH-EAST\', "DipDir2")',
            'INPUT': outputs['CalcolatoreDiCampiDip2Northeast']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalcolatoreDiCampiDip2Southeast'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(20)
        if feedback.isCanceled():
            return {}

        # Calcolatore di campi (DIP2) (SOUTH-WEST)
        alg_params = {
            'FIELD_LENGTH': 15,
            'FIELD_NAME': 'DipDir2',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # Testo (stringa)
            'FORMULA': 'if("DIP_DIR" = \'SUD-OVEST\' OR "DIP_DIR" = \'sud-ovest\' OR "DIP_DIR" = \'Sud-ovest\' OR "DIP_DIR" = \'Sud-Ovest\' OR "DIP_DIR" = \'south-west\' OR "DIP_DIR" = \'South-west\' OR "DIP_DIR" = \'South-West\' OR "DIP_DIR" = \'SOUTH-WEST\' OR "DIP_DIR" = \'sw\' OR "DIP_DIR" = \'Sw\' OR "DIP_DIR" = \'SW\' OR "DIP_DIR" = \'sud-sud-ovest\' OR "DIP_DIR" = \'Sud-sud-ovest\' OR "DIP_DIR" = \'Sud-Sud-Ovest\' OR "DIP_DIR" = \'SUD-SUD-OVEST\' OR "DIP_DIR" = \'south-south-west\' OR "DIP_DIR" = \'South-south-west\' OR "DIP_DIR" = \'South-South-West\' OR "DIP_DIR" = \'SOUTH-SOUTH-WEST\' OR "DIP_DIR" = \'ssw\' OR "DIP_DIR" = \'Ssw\' OR "DIP_DIR" = \'SSW\' OR "DIP_DIR" = \'ovest-sud-ovest\' OR "DIP_DIR" = \'Ovest-sud-ovest\' OR "DIP_DIR" = \'Ovest-Sud-Ovest\' OR "DIP_DIR" = \'OVEST-SUD-OVEST\' OR "DIP_DIR" = \'west-south-west\' OR "DIP_DIR" = \'West-south-west\' OR "DIP_DIR" = \'West-South-West\' OR "DIP_DIR" = \'WEST-SOUTH-WEST\' OR "DIP_DIR" = \'wsw\' OR "DIP_DIR" = \'Wsw\' OR "DIP_DIR" = \'WSW\' OR "DIP_DIR" = \'ovest\' OR "DIP_DIR" = \'Ovest\' OR  "DIP_DIR" = \'OVEST\' OR "DIP_DIR" = \'west\' OR "DIP_DIR" = \'West\' OR "DIP_DIR" = \'WEST\' OR "DIP_DIR" = \'o\' OR "DIP_DIR" = \'O\' OR "DIP_DIR" = \'w\' OR "DIP_DIR" = \'W\', \'SOUTH-WEST\', "DipDir2")',
            'INPUT': outputs['CalcolatoreDiCampiDip2Southeast']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalcolatoreDiCampiDip2Southwest'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(21)
        if feedback.isCanceled():
            return {}

        # Calcolatore di campi (DIP2) (NORTH-WEST)
        alg_params = {
            'FIELD_LENGTH': 15,
            'FIELD_NAME': 'DipDir2',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # Testo (stringa)
            'FORMULA': 'if("DIP_DIR" = \'NORD-OVEST\' OR "DIP_DIR" = \'nord-ovest\' OR "DIP_DIR" = \'Nord-ovest\' OR "DIP_DIR" = \'Nord-Ovest\' OR "DIP_DIR" = \'north-west\' OR "DIP_DIR" = \'North-west\' OR "DIP_DIR" = \'North-West\' OR "DIP_DIR" = \'NORTH-WEST\' OR "DIP_DIR" = \'nw\' OR "DIP_DIR" = \'Nw\' OR "DIP_DIR" = \'NW\' OR "DIP_DIR" = \'nord-nord-ovest\' OR "DIP_DIR" = \'Nord-nord-ovest\' OR "DIP_DIR" = \'Nord-Nord-Ovest\' OR "DIP_DIR" = \'NORD-NORD-OVEST\' OR "DIP_DIR" = \'north-north-west\' OR "DIP_DIR" = \'North-north-west\' OR "DIP_DIR" = \'North-North-West\' OR "DIP_DIR" = \'NORTH-NORTH-WEST\' OR "DIP_DIR" = \'nnw\' OR "DIP_DIR" = \'Nnw\' OR "DIP_DIR" = \'NNW\' OR "DIP_DIR" = \'ovest-nord-ovest\' OR "DIP_DIR" = \'Ovest-nord-ovest\' OR "DIP_DIR" = \'Ovest-Nord-Ovest\' OR "DIP_DIR" = \'OVEST-NORD-OVEST\' OR "DIP_DIR" = \'west-north-west\' OR "DIP_DIR" = \'West-north-west\' OR "DIP_DIR" = \'West-North-West\' OR "DIP_DIR" = \'WEST-NORTH-WEST\' OR "DIP_DIR" = \'wnw\' OR "DIP_DIR" = \'Wnw\' OR "DIP_DIR" = \'WNW\' OR "DIP_DIR" = \'nord\' OR "DIP_DIR" = \'Nord\' OR "DIP_DIR" = \'NORD\' OR "DIP_DIR" = \'north\' OR "DIP_DIR" = \'North\' OR "DIP_DIR" = \'NORTH\' OR "DIP_DIR" = \'n\' OR "DIP_DIR" = \'N\', \'NORTH-WEST\', "DipDir2")',
            'INPUT': outputs['CalcolatoreDiCampiDip2Southwest']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalcolatoreDiCampiDip2Northwest'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(22)
        if feedback.isCanceled():
            return {}

        # Calcolatore di campi (FLIP?)
        alg_params = {
            'FIELD_LENGTH': 8,
            'FIELD_NAME': 'TO_FLIP',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # Testo (stringa)
            'FORMULA': 'if("DIRECTION" = \'N\' AND "DipDir" = \'WEST\' OR "DIRECTION" = "E" AND "DipDir" = \'NORTH\' OR "DIRECTION" = \'S\' AND "DipDir" = \'EAST\' OR "DIRECTION" = \'W\' AND "DipDir" = \'SOUTH\' OR "DIRECTION2" = \'N-E\' AND "DipDir2" = \'NORTH-WEST\' OR "DIRECTION2" = \'S-E\' AND "DipDir2" = \'NORTH-EAST\' OR "DIRECTION2" = \'S-W\' AND "DipDir2" = \'SOUTH-EAST\' OR "DIRECTION2" = \'N-W\' AND "DipDir2" = \'SOUTH-WEST\', \'FLIP\', \'NO_FLIP\')',
            'INPUT': outputs['CalcolatoreDiCampiDip2Northwest']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalcolatoreDiCampiFlip'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(23)
        if feedback.isCanceled():
            return {}

        # Estrai tramite espressione (FLIP)
        alg_params = {
            'EXPRESSION': ' "TO_FLIP" = \'FLIP\'',
            'INPUT': outputs['CalcolatoreDiCampiFlip']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['EstraiTramiteEspressioneFlip'] = processing.run('native:extractbyexpression', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(24)
        if feedback.isCanceled():
            return {}

        # Estrai tramite espressione (NO_FLIP)
        alg_params = {
            'EXPRESSION': ' "TO_FLIP" = \'NO_FLIP\'',
            'INPUT': outputs['CalcolatoreDiCampiFlip']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['EstraiTramiteEspressioneNo_flip'] = processing.run('native:extractbyexpression', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(25)
        if feedback.isCanceled():
            return {}

        # Inverti verso linea
        alg_params = {
            'INPUT': outputs['EstraiTramiteEspressioneFlip']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['InvertiVersoLinea'] = processing.run('native:reverselinedirection', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(26)
        if feedback.isCanceled():
            return {}

        # Fondi vettori (merge)
        alg_params = {
            'CRS': None,
            'LAYERS': [outputs['EstraiTramiteEspressioneNo_flip']['OUTPUT'],outputs['InvertiVersoLinea']['OUTPUT']],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['FondiVettoriMerge'] = processing.run('native:mergevectorlayers', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(27)
        if feedback.isCanceled():
            return {}

        # Raggruppa geometrie
        alg_params = {
            'FIELD': ['AUTO'],
            'INPUT': outputs['FondiVettoriMerge']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RaggruppaGeometrie'] = processing.run('native:collect', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(28)
        if feedback.isCanceled():
            return {}

        # Elimina campo(i)
        alg_params = {
            'COLUMN': ['AUTO','BEARING','DIRECTION','DipDir','DIRECTION2','DipDir2','layer','path'],
            'INPUT': outputs['RaggruppaGeometrie']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['EliminaCampoi'] = processing.run('qgis:deletecolumn', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(29)
        if feedback.isCanceled():
            return {}

        # Rinomina campo (Cinematica)
        alg_params = {
            'FIELD': parameters['Kinematic'],
            'INPUT': outputs['EliminaCampoi']['OUTPUT'],
            'NEW_NAME': '_K_N_',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RinominaCampoCinematica'] = processing.run('native:renametablefield', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(30)
        if feedback.isCanceled():
            return {}

        # Calcolatore di campi (lunghezza)
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'Length(km)',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 0,  # Decimale (doppia precisione)
            'FORMULA': '$length/1000',
            'INPUT': outputs['RinominaCampoCinematica']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalcolatoreDiCampiLunghezza'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(31)
        if feedback.isCanceled():
            return {}

        # Calcolatore di campi (Dimensione Buffer)
        alg_params = {
            'FIELD_LENGTH': 0,
            'FIELD_NAME': 'BuffDim',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 1,  # Intero (32 bit)
            'FORMULA': 'if( "D_A_______" > 70, 1, if("D_A_______" <= 70 and "D_A_______" > 40, 5, if( "D_A_______" < 40, 10, CASE WHEN substr("_K_N_",1,3)=\'nor\' THEN 5 WHEN substr("_K_N_",1,3)=\'Nor\' THEN 5 WHEN substr("_K_N_",1,3)=\'NOR\' THEN 5 WHEN substr("_K_N_",1,3)=\'nrm\' THEN 5 WHEN substr("_K_N_",1,3)=\'Nrm\' THEN 5 WHEN substr("_K_N_",1,3)=\'NRM\' THEN 5 WHEN substr("_K_N_",1,3)=\'est\' THEN 5 WHEN substr("_K_N_",1,3)=\'Est\' THEN 5 WHEN substr("_K_N_",1,3)=\'EST\' THEN 5 WHEN substr("_K_N_",1,3)=\'ext\' THEN 5 WHEN substr("_K_N_",1,3)=\'Ext\' THEN 5 WHEN substr("_K_N_",1,3)=\'EXT\' THEN 5 WHEN substr("_K_N_",1,3)=\'dis\' THEN 5 WHEN substr("_K_N_",1,3)=\'Dis\' THEN 5 WHEN substr("_K_N_",1,3)=\'DIS\' THEN 5 WHEN substr("_K_N_",1,1)=\'n\' THEN 5 WHEN substr("_K_N_",1,1)=\'N\' THEN 5 WHEN substr("_K_N_",1,3)=\'tra\' THEN 1 WHEN substr("_K_N_",1,3)=\'Tra\' THEN 1 WHEN substr("_K_N_",1,3)=\'TRA\' THEN 1 WHEN substr("_K_N_",1,3)=\'str\' THEN 1 WHEN substr("_K_N_",1,3)=\'Str\' THEN 1 WHEN substr("_K_N_",1,3)=\'STR\' THEN 1 WHEN substr("_K_N_",1,2)=\'ss\' THEN 1 WHEN substr("_K_N_",1,2)=\'Ss\' THEN 1 WHEN substr("_K_N_",1,2)=\'SS\' THEN 1 ELSE 10 END)))',
            'INPUT': outputs['CalcolatoreDiCampiLunghezza']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalcolatoreDiCampiDimensioneBuffer'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(32)
        if feedback.isCanceled():
            return {}

        # Buffer lato singolo
        alg_params = {
            'DISTANCE': QgsProperty.fromExpression('"BuffDim"/100'),
            'INPUT': outputs['CalcolatoreDiCampiDimensioneBuffer']['OUTPUT'],
            'JOIN_STYLE': 2,  # Smussato
            'MITER_LIMIT': 1,
            'SEGMENTS': 15,
            'SIDE': 1,  # Destra
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['BufferLatoSingolo'] = processing.run('native:singlesidedbuffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(33)
        if feedback.isCanceled():
            return {}

        # Estrazione per posizione
        alg_params = {
            'INPUT': outputs['RinominaCampoProfondit']['OUTPUT'],
            'INTERSECT': outputs['BufferLatoSingolo']['OUTPUT'],
            'PREDICATE': [0,6],  # interseca,sono contenuti
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['EstrazionePerPosizione'] = processing.run('native:extractbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(34)
        if feedback.isCanceled():
            return {}

        # Unire gli attributi per luogo
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'INPUT': outputs['EstrazionePerPosizione']['OUTPUT'],
            'JOIN': outputs['BufferLatoSingolo']['OUTPUT'],
            'JOIN_FIELDS': ['Name'],
            'METHOD': 2,  # Prendi solamente gli attributi dell'elemento con maggiore sovrapposizione (uno-a-uno)
            'PREDICATE': [0,5],  # interseca,sono contenuti
            'PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['UnireGliAttributiPerLuogo'] = processing.run('native:joinattributesbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(35)
        if feedback.isCanceled():
            return {}

        # Calcolatore Campi (Spessore sismogenico)
        alg_params = {
            'FIELD_LENGTH': 0,
            'FIELD_NAME': 'Seis_thick',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0,  # Decimale (doppia precisione)
            'FORMULA': 'array_get(array_sort(array_agg("D_F_______",group_by:= "Name" )),floor((array_length(array_agg("D_F_______",group_by:= "Name"))*90)/100))-array_get(array_sort(array_agg("D_F_______" ,group_by:= "Name")),floor((array_length(array_agg("D_F_______",group_by:= "Name"))*10)/100))\r\n',
            'INPUT': outputs['UnireGliAttributiPerLuogo']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalcolatoreCampiSpessoreSismogenico'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(36)
        if feedback.isCanceled():
            return {}

        # Unire gli attributi per località (sintesi)
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'INPUT': outputs['BufferLatoSingolo']['OUTPUT'],
            'JOIN': outputs['CalcolatoreCampiSpessoreSismogenico']['OUTPUT'],
            'JOIN_FIELDS': ['D_F_______'],
            'PREDICATE': [0,1],  # interseca,contiene
            'SUMMARIES': [2,3],  # min,max
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['UnireGliAttributiPerLocalitSintesi'] = processing.run('qgis:joinbylocationsummary', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(37)
        if feedback.isCanceled():
            return {}

        # Unire gli attributi per luogo (add seism thick)
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'INPUT': outputs['UnireGliAttributiPerLocalitSintesi']['OUTPUT'],
            'JOIN': outputs['CalcolatoreCampiSpessoreSismogenico']['OUTPUT'],
            'JOIN_FIELDS': ['Seis_thick'],
            'METHOD': 1,  # Prendi solamente gli attributi del primo elemento corrispondente (uno-a-uno)
            'PREDICATE': [0,5],  # interseca,sono contenuti
            'PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['UnireGliAttributiPerLuogoAddSeismThick'] = processing.run('native:joinattributesbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(38)
        if feedback.isCanceled():
            return {}

        # Rinomina campo (K_N)
        alg_params = {
            'FIELD': '_K_N_',
            'INPUT': outputs['UnireGliAttributiPerLuogoAddSeismThick']['OUTPUT'],
            'NEW_NAME': 'Kinematic',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RinominaCampoK_n'] = processing.run('native:renametablefield', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(39)
        if feedback.isCanceled():
            return {}

        # Rinomina campo (D_A)
        alg_params = {
            'FIELD': 'D_A_______',
            'INPUT': outputs['RinominaCampoK_n']['OUTPUT'],
            'NEW_NAME': 'Dip Angle',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RinominaCampoD_a'] = processing.run('native:renametablefield', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(40)
        if feedback.isCanceled():
            return {}

        # Rinomina campo (D_F_min)
        alg_params = {
            'FIELD': 'D_F________min',
            'INPUT': outputs['RinominaCampoD_a']['OUTPUT'],
            'NEW_NAME': 'Depth min',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RinominaCampoD_f_min'] = processing.run('native:renametablefield', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(41)
        if feedback.isCanceled():
            return {}

        # Rinomina campo (D_F_max)
        alg_params = {
            'FIELD': 'D_F________max',
            'INPUT': outputs['RinominaCampoD_f_min']['OUTPUT'],
            'NEW_NAME': 'Depth max',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RinominaCampoD_f_max'] = processing.run('native:renametablefield', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(42)
        if feedback.isCanceled():
            return {}

        # Calcolatore di campi (width)
        alg_params = {
            'FIELD_LENGTH': 0,
            'FIELD_NAME': 'Width',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0,  # Decimale (doppia precisione)
            'FORMULA': '"Seis_thick"/sin(radians("Dip Angle"))',
            'INPUT': outputs['RinominaCampoD_f_max']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalcolatoreDiCampiWidth'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(43)
        if feedback.isCanceled():
            return {}

        # Calcolatore di campi (area rottura)
        alg_params = {
            'FIELD_LENGTH': 0,
            'FIELD_NAME': 'Rupt_area',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0,  # Decimale (doppia precisione)
            'FORMULA': '"Width"*"Length(km)"',
            'INPUT': outputs['CalcolatoreDiCampiWidth']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalcolatoreDiCampiAreaRottura'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(44)
        if feedback.isCanceled():
            return {}

        # Calcolatore di campi (M - length)
        alg_params = {
            'FIELD_LENGTH': 0,
            'FIELD_NAME': 'M (length)',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0,  # Decimale (doppia precisione)
            'FORMULA': 'CASE WHEN substr("Kinematic",1,3)=\'nor\' THEN 4.86+1.32*log10("Length(km)") WHEN substr("Kinematic",1,3)=\'Nor\' THEN 4.86+1.32*log10("Length(km)") WHEN substr("Kinematic",1,3)=\'NOR\' THEN 4.86+1.32*log10("Length(km)") WHEN substr("Kinematic",1,3)=\'nrm\' THEN 4.86+1.32*log10("Length(km)") WHEN substr("Kinematic",1,3)=\'Nrm\' THEN 4.86+1.32*log10("Length(km)") WHEN substr("Kinematic",1,3)=\'NRM\' THEN 4.86+1.32*log10("Length(km)") WHEN substr("Kinematic",1,3)=\'est\' THEN 4.86+1.32*log10("Length(km)") WHEN substr("Kinematic",1,3)=\'Est\' THEN 4.86+1.32*log10("Length(km)") WHEN substr("Kinematic",1,3)=\'EST\' THEN 4.86+1.32*log10("Length(km)") WHEN substr("Kinematic",1,3)=\'ext\' THEN 4.86+1.32*log10("Length(km)") WHEN substr("Kinematic",1,3)=\'Ext\' THEN 4.86+1.32*log10("Length(km)") WHEN substr("Kinematic",1,3)=\'EXT\' THEN 4.86+1.32*log10("Length(km)") WHEN substr("Kinematic",1,3)=\'dis\' THEN 4.86+1.32*log10("Length(km)") WHEN substr("Kinematic",1,3)=\'Dis\' THEN 4.86+1.32*log10("Length(km)") WHEN substr("Kinematic",1,3)=\'DIS\' THEN 4.86+1.32*log10("Length(km)") WHEN substr("Kinematic",1,1)=\'n\' THEN 4.86+1.32*log10("Length(km)") WHEN substr("Kinematic",1,1)=\'N\' THEN 4.86+1.32*log10("Length(km)") WHEN substr("Kinematic",1,3)=\'tra\' THEN 5.16+1.12*log10("Length(km)") WHEN substr("Kinematic",1,3)=\'Tra\' THEN 5.16+1.12*log10("Length(km)") WHEN substr("Kinematic",1,3)=\'TRA\' THEN 5.16+1.12*log10("Length(km)") WHEN substr("Kinematic",1,3)=\'str\' THEN 5.16+1.12*log10("Length(km)") WHEN substr("Kinematic",1,3)=\'Str\' THEN 5.16+1.12*log10("Length(km)") WHEN substr("Kinematic",1,3)=\'STR\' THEN 5.16+1.12*log10("Length(km)") WHEN substr("Kinematic",1,2)=\'ss\' THEN 5.16+1.12*log10("Length(km)") WHEN substr("Kinematic",1,2)=\'Ss\' THEN 5.16+1.12*log10("Length(km)") WHEN substr("Kinematic",1,2)=\'SS\' THEN 5.16+1.12*log10("Length(km)") ELSE 5+1.22*log10("Length(km)") END',
            'INPUT': outputs['CalcolatoreDiCampiAreaRottura']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalcolatoreDiCampiMLength'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(45)
        if feedback.isCanceled():
            return {}

        # Calcolatore di campi (M - rupture area)
        alg_params = {
            'FIELD_LENGTH': 0,
            'FIELD_NAME': 'M (r_area)',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0,  # Decimale (doppia precisione)
            'FORMULA': 'CASE WHEN substr("Kinematic",1,3)=\'nor\' THEN 3.93+1.02*log10("Rupt_area") WHEN substr("Kinematic",1,3)=\'Nor\' THEN 3.93+1.02*log10("Rupt_area") WHEN substr("Kinematic",1,3)=\'NOR\' THEN 3.93+1.02*log10("Rupt_area") WHEN substr("Kinematic",1,3)=\'nrm\' THEN 3.93+1.02*log10("Rupt_area") WHEN substr("Kinematic",1,3)=\'Nrm\' THEN 3.93+1.02*log10("Rupt_area") WHEN substr("Kinematic",1,3)=\'NRM\' THEN 3.93+1.02*log10("Rupt_area") WHEN substr("Kinematic",1,3)=\'est\' THEN 3.93+1.02*log10("Rupt_area") WHEN substr("Kinematic",1,3)=\'Est\' THEN 3.93+1.02*log10("Rupt_area") WHEN substr("Kinematic",1,3)=\'EST\' THEN 3.93+1.02*log10("Rupt_area") WHEN substr("Kinematic",1,3)=\'ext\' THEN 3.93+1.02*log10("Rupt_area") WHEN substr("Kinematic",1,3)=\'Ext\' THEN 3.93+1.02*log10("Rupt_area") WHEN substr("Kinematic",1,3)=\'EXT\' THEN 3.93+1.02*log10("Rupt_area") WHEN substr("Kinematic",1,3)=\'dis\' THEN 3.93+1.02*log10("Rupt_area") WHEN substr("Kinematic",1,3)=\'Dis\' THEN 3.93+1.02*log10("Rupt_area") WHEN substr("Kinematic",1,3)=\'DIS\' THEN 3.93+1.02*log10("Rupt_area") WHEN substr("Kinematic",1,1)=\'n\' THEN 3.93+1.02*log10("Rupt_area") WHEN substr("Kinematic",1,1)=\'N\' THEN 3.93+1.02*log10("Rupt_area") WHEN substr("Kinematic",1,3)=\'tra\' THEN 3.98+1.02*log10("Rupt_area") WHEN substr("Kinematic",1,3)=\'Tra\' THEN 3.98+1.02*log10("Rupt_area") WHEN substr("Kinematic",1,3)=\'TRA\' THEN 3.98+1.02*log10("Rupt_area") WHEN substr("Kinematic",1,3)=\'str\' THEN 3.98+1.02*log10("Rupt_area") WHEN substr("Kinematic",1,3)=\'Str\' THEN 3.98+1.02*log10("Rupt_area") WHEN substr("Kinematic",1,3)=\'STR\' THEN 3.98+1.02*log10("Rupt_area") WHEN substr("Kinematic",1,2)=\'ss\' THEN 3.98+1.02*log10("Rupt_area") WHEN substr("Kinematic",1,2)=\'Ss\' THEN 3.98+1.02*log10("Rupt_area") WHEN substr("Kinematic",1,2)=\'SS\' THEN 3.98+1.02*log10("Rupt_area") ELSE 4.33+0.80*log10("Rupt_area") END',
            'INPUT': outputs['CalcolatoreDiCampiMLength']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalcolatoreDiCampiMRuptureArea'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(46)
        if feedback.isCanceled():
            return {}

        # Calcolatore di campi (M - width)
        alg_params = {
            'FIELD_LENGTH': 0,
            'FIELD_NAME': 'M (width)',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0,  # Decimale (doppia precisione)
            'FORMULA': 'CASE WHEN substr("Kinematic",1,3)=\'nor\' THEN 4.04+2.11*log10("Width") WHEN substr("Kinematic",1,3)=\'Nor\' THEN 4.04+2.11*log10("Width") WHEN substr("Kinematic",1,3)=\'NOR\' THEN 4.04+2.11*log10("Width") WHEN substr("Kinematic",1,3)=\'nrm\' THEN 4.04+2.11*log10("Width") WHEN substr("Kinematic",1,3)=\'Nrm\' THEN 4.04+2.11*log10("Width") WHEN substr("Kinematic",1,3)=\'NRM\' THEN 4.04+2.11*log10("Width") WHEN substr("Kinematic",1,3)=\'est\' THEN 4.04+2.11*log10("Width") WHEN substr("Kinematic",1,3)=\'Est\' THEN 4.04+2.11*log10("Width") WHEN substr("Kinematic",1,3)=\'EST\' THEN 4.04+2.11*log10("Width") WHEN substr("Kinematic",1,3)=\'ext\' THEN 4.04+2.11*log10("Width") WHEN substr("Kinematic",1,3)=\'Ext\' THEN 4.04+2.11*log10("Width") WHEN substr("Kinematic",1,3)=\'EXT\' THEN 4.04+2.11*log10("Width") WHEN substr("Kinematic",1,3)=\'dis\' THEN 4.04+2.11*log10("Width") WHEN substr("Kinematic",1,3)=\'Dis\' THEN 4.04+2.11*log10("Width") WHEN substr("Kinematic",1,3)=\'DIS\' THEN 4.04+2.11*log10("Width") WHEN substr("Kinematic",1,1)=\'n\' THEN 4.04+2.11*log10("Width") WHEN substr("Kinematic",1,1)=\'N\' THEN 4.04+2.11*log10("Width") WHEN substr("Kinematic",1,3)=\'tra\' THEN 3.80+2.59*log10("Width") WHEN substr("Kinematic",1,3)=\'Tra\' THEN 3.80+2.59*log10("Width") WHEN substr("Kinematic",1,3)=\'TRA\' THEN 3.80+2.59*log10("Width") WHEN substr("Kinematic",1,3)=\'str\' THEN 3.80+2.59*log10("Width") WHEN substr("Kinematic",1,3)=\'Str\' THEN 3.80+2.59*log10("Width") WHEN substr("Kinematic",1,3)=\'STR\' THEN 3.80+2.59*log10("Width") WHEN substr("Kinematic",1,2)=\'ss\' THEN 3.80+2.59*log10("Width") WHEN substr("Kinematic",1,2)=\'Ss\' THEN 3.80+2.59*log10("Width") WHEN substr("Kinematic",1,2)=\'SS\' THEN 3.80+2.59*log10("Width") ELSE 4.37+1.95*log10("Width") END',
            'INPUT': outputs['CalcolatoreDiCampiMRuptureArea']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalcolatoreDiCampiMWidth'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(47)
        if feedback.isCanceled():
            return {}

        # Calcolatore di campi (max disp. len.)
        alg_params = {
            'FIELD_LENGTH': 0,
            'FIELD_NAME': 'max_dis(m)',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0,  # Decimale (doppia precisione)
            'FORMULA': 'CASE WHEN substr("Kinematic",1,3)=\'nor\' THEN 10^(-1.98+1.51*log10("Length(km)")) WHEN substr("Kinematic",1,3)=\'Nor\' THEN 10^(-1.98+1.51*log10("Length(km)")) WHEN substr("Kinematic",1,3)=\'NOR\' THEN 10^(-1.98+1.51*log10("Length(km)")) WHEN substr("Kinematic",1,3)=\'nrm\' THEN 10^(-1.98+1.51*log10("Length(km)")) WHEN substr("Kinematic",1,3)=\'Nrm\' THEN 10^(-1.98+1.51*log10("Length(km)")) WHEN substr("Kinematic",1,3)=\'NRM\' THEN 10^(-1.98+1.51*log10("Length(km)")) WHEN substr("Kinematic",1,3)=\'est\' THEN 10^(-1.98+1.51*log10("Length(km)")) WHEN substr("Kinematic",1,3)=\'Est\' THEN 10^(-1.98+1.51*log10("Length(km)")) WHEN substr("Kinematic",1,3)=\'EST\' THEN 10^(-1.98+1.51*log10("Length(km)")) WHEN substr("Kinematic",1,3)=\'ext\' THEN 10^(-1.98+1.51*log10("Length(km)")) WHEN substr("Kinematic",1,3)=\'Ext\' THEN 10^(-1.98+1.51*log10("Length(km)")) WHEN substr("Kinematic",1,3)=\'EXT\' THEN 10^(-1.98+1.51*log10("Length(km)")) WHEN substr("Kinematic",1,3)=\'dis\' THEN 10^(-1.98+1.51*log10("Length(km)")) WHEN substr("Kinematic",1,3)=\'Dis\' THEN 10^(-1.98+1.51*log10("Length(km)")) WHEN substr("Kinematic",1,3)=\'DIS\' THEN 10^(-1.98+1.51*log10("Length(km)")) WHEN substr("Kinematic",1,1)=\'n\' THEN 10^(-1.98+1.51*log10("Length(km)")) WHEN substr("Kinematic",1,1)=\'N\' THEN 10^(-1.98+1.51*log10("Length(km)")) WHEN substr("Kinematic",1,3)=\'tra\' THEN 10^(-1.69+1.16*log10("Length(km)")) WHEN substr("Kinematic",1,3)=\'Tra\' THEN 10^(-1.69+1.16*log10("Length(km)")) WHEN substr("Kinematic",1,3)=\'TRA\' THEN 10^(-1.69+1.16*log10("Length(km)")) WHEN substr("Kinematic",1,3)=\'str\' THEN 10^(-1.69+1.16*log10("Length(km)")) WHEN substr("Kinematic",1,3)=\'Str\' THEN 10^(-1.69+1.16*log10("Length(km)")) WHEN substr("Kinematic",1,3)=\'STR\' THEN 10^(-1.69+1.16*log10("Length(km)")) WHEN substr("Kinematic",1,2)=\'ss\' THEN 10^(-1.69+1.16*log10("Length(km)")) WHEN substr("Kinematic",1,2)=\'Ss\' THEN 10^(-1.69+1.16*log10("Length(km)")) WHEN substr("Kinematic",1,2)=\'SS\' THEN 10^(-1.69+1.16*log10("Length(km)")) ELSE 10^(-0.44+0.42*log10("Length(km)")) END',
            'INPUT': outputs['CalcolatoreDiCampiMWidth']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalcolatoreDiCampiMaxDispLen'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(48)
        if feedback.isCanceled():
            return {}

        # Calcolatore di campi (av.disp. leng.)
        alg_params = {
            'FIELD_LENGTH': 0,
            'FIELD_NAME': 'av_disp(m)',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0,  # Decimale (doppia precisione)
            'FORMULA': 'CASE WHEN substr("Kinematic",1,3)=\'nor\' THEN 10^(-1.99+1.24*log10("Length(km)")) WHEN substr("Kinematic",1,3)=\'Nor\' THEN 10^(-1.99+1.24*log10("Length(km)")) WHEN substr("Kinematic",1,3)=\'NOR\' THEN 10^(-1.99+1.24*log10("Length(km)")) WHEN substr("Kinematic",1,3)=\'nrm\' THEN 10^(-1.99+1.24*log10("Length(km)")) WHEN substr("Kinematic",1,3)=\'Nrm\' THEN 10^(-1.99+1.24*log10("Length(km)")) WHEN substr("Kinematic",1,3)=\'NRM\' THEN 10^(-1.99+1.24*log10("Length(km)")) WHEN substr("Kinematic",1,3)=\'est\' THEN 10^(-1.99+1.24*log10("Length(km)")) WHEN substr("Kinematic",1,3)=\'Est\' THEN 10^(-1.99+1.24*log10("Length(km)")) WHEN substr("Kinematic",1,3)=\'EST\' THEN 10^(-1.99+1.24*log10("Length(km)")) WHEN substr("Kinematic",1,3)=\'ext\' THEN 10^(-1.99+1.24*log10("Length(km)")) WHEN substr("Kinematic",1,3)=\'Ext\' THEN 10^(-1.99+1.24*log10("Length(km)")) WHEN substr("Kinematic",1,3)=\'EXT\' THEN 10^(-1.99+1.24*log10("Length(km)")) WHEN substr("Kinematic",1,3)=\'dis\' THEN 10^(-1.99+1.24*log10("Length(km)")) WHEN substr("Kinematic",1,3)=\'Dis\' THEN 10^(-1.99+1.24*log10("Length(km)")) WHEN substr("Kinematic",1,3)=\'DIS\' THEN 10^(-1.99+1.24*log10("Length(km)")) WHEN substr("Kinematic",1,1)=\'n\' THEN 10^(-1.99+1.24*log10("Length(km)")) WHEN substr("Kinematic",1,1)=\'N\' THEN 10^(-1.99+1.24*log10("Length(km)")) WHEN substr("Kinematic",1,3)=\'tra\' THEN 10^(-1.70+1.04*log10("Length(km)")) WHEN substr("Kinematic",1,3)=\'Tra\' THEN 10^(-1.70+1.04*log10("Length(km)")) WHEN substr("Kinematic",1,3)=\'TRA\' THEN 10^(-1.70+1.04*log10("Length(km)")) WHEN substr("Kinematic",1,3)=\'str\' THEN 10^(-1.70+1.04*log10("Length(km)")) WHEN substr("Kinematic",1,3)=\'Str\' THEN 10^(-1.70+1.04*log10("Length(km)")) WHEN substr("Kinematic",1,3)=\'STR\' THEN 10^(-1.70+1.04*log10("Length(km)")) WHEN substr("Kinematic",1,2)=\'ss\' THEN 10^(-1.70+1.04*log10("Length(km)")) WHEN substr("Kinematic",1,2)=\'Ss\' THEN 10^(-1.70+1.04*log10("Length(km)")) WHEN substr("Kinematic",1,2)=\'SS\' THEN 10^(-1.70+1.04*log10("Length(km)")) ELSE 10^(-0.60+0.31*log10("Length(km)")) END',
            'INPUT': outputs['CalcolatoreDiCampiMaxDispLen']['OUTPUT'],
            'OUTPUT': parameters['BufferWithEstimatedParameters']
        }
        outputs['CalcolatoreDiCampiAvdispLeng'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['BufferWithEstimatedParameters'] = outputs['CalcolatoreDiCampiAvdispLeng']['OUTPUT']
        return results

    def name(self):
        return 'Wells and Coppersmith estimation'

    def displayName(self):
        return 'Wells and Coppersmith estimation'

    def group(self):
        return ''

    def groupId(self):
        return ''

    def shortHelpString(self):
        return """<html><body><p>First faults are flipped respect to the dip direction. Than the alghoritm create buffer for each line. Earthquakes from a shape (points) are selected and releted to the buffers (point contained in the buffer area). Values of 10% and 90% of each selection are used to estimate the thickness of the seismogenic layer. </p>
<h2>Parametri in ingresso
</h2>
<h3>Faults</h3>
<p>Linear shape of faults</p>
<h3>Eqs</h3>
<p>Earthquakes to be associated with faults</p>
<h3>Depth field (km)</h3>
<p>Field containing earthquakes depth in km</p>
<h3>Dip angle</h3>
<p>Field containing dip angle for each fault</p>
<h3>Dip direction</h3>
<p>Field containing dip direction for each fault (string refered to wind rose)</p>
<h3>Kinematic</h3>
<p>Field containing kinematic for each fault</p>
<br><p align="right">Autore algoritmo: Pietrolungo Federico, Talone Donato</p><p align="right">Versione algoritmo: 1.0</p></body></html>"""

    def createInstance(self):
        return WellsAndCoppersmithEstimation()
