package com.bilingual.lessonplanner.utils

import com.bilingual.lessonplanner.domain.model.*
import com.google.gson.Gson
import com.google.gson.JsonObject
import com.google.gson.JsonParser
import com.google.gson.reflect.TypeToken

object LessonJsonParser {
    private val gson = Gson()
    
    fun parse(lessonJson: String?): LessonJsonData? {
        if (lessonJson.isNullOrBlank()) {
            return null
        }
        
        return try {
            val jsonElement = JsonParser.parseString(lessonJson)
            if (!jsonElement.isJsonObject) {
                Logger.w("lesson_json is not a JSON object")
                return null
            }
            
            val rootObject = jsonElement.asJsonObject
            
            // Parse days
            val daysMap = mutableMapOf<String, DayData>()
            
            if (rootObject.has("days") && rootObject.get("days").isJsonObject) {
                val daysObject = rootObject.getAsJsonObject("days")
                
                daysObject.keySet().forEach { dayName ->
                    val dayElement = daysObject.get(dayName)
                    if (dayElement.isJsonObject) {
                        val dayData = parseDayData(dayElement.asJsonObject)
                        if (dayData != null) {
                            daysMap[dayName] = dayData
                        }
                    }
                }
            }
            
            LessonJsonData(days = daysMap)
        } catch (e: Exception) {
            Logger.e("Failed to parse lesson_json", e)
            null
        }
    }
    
    private fun parseDayData(dayObject: JsonObject): DayData? {
        val slotsMap = mutableMapOf<String, SlotData>()
        
        dayObject.keySet().forEach { slotKey ->
            val slotElement = dayObject.get(slotKey)
            if (slotElement.isJsonObject) {
                val slotData = parseSlotData(slotElement.asJsonObject)
                if (slotData != null) {
                    slotsMap[slotKey] = slotData
                }
            }
        }
        
        return DayData(slots = slotsMap)
    }
    
    private fun parseSlotData(slotObject: JsonObject): SlotData? {
        val objectives = parseObjectiveData(slotObject.get("objectives"))
        val vocabulary = parseStringList(slotObject.get("vocabulary"))
        val vocabularyCognates = parseStringList(slotObject.get("vocabulary_cognates"))
        val sentenceFrames = parseStringList(slotObject.get("sentence_frames"))
        val materialsNeeded = parseStringList(slotObject.get("materials_needed"))
        val instructionSteps = parseInstructionSteps(slotObject.get("instruction_steps"))
        
        return SlotData(
            objectives = objectives,
            vocabulary = vocabulary,
            vocabulary_cognates = vocabularyCognates,
            sentence_frames = sentenceFrames,
            materials_needed = materialsNeeded,
            instruction_steps = instructionSteps
        )
    }
    
    private fun parseObjectiveData(element: com.google.gson.JsonElement?): ObjectiveData? {
        if (element == null || !element.isJsonObject) {
            return null
        }
        
        val obj = element.asJsonObject
        return ObjectiveData(
            content = obj.get("content")?.takeIf { it.isJsonPrimitive }?.asString,
            language = obj.get("language")?.takeIf { it.isJsonPrimitive }?.asString
        )
    }
    
    private fun parseStringList(element: com.google.gson.JsonElement?): List<String>? {
        if (element == null || !element.isJsonArray) {
            return null
        }
        
        return try {
            val array = element.asJsonArray
            array.mapNotNull { 
                if (it.isJsonPrimitive) it.asString else null
            }
        } catch (e: Exception) {
            Logger.w("Failed to parse string list", e)
            null
        }
    }
    
    private fun parseInstructionSteps(element: com.google.gson.JsonElement?): List<InstructionStepData>? {
        if (element == null || !element.isJsonArray) {
            return null
        }
        
        return try {
            val array = element.asJsonArray
            array.mapNotNull { stepElement ->
                if (stepElement.isJsonObject) {
                    val stepObj = stepElement.asJsonObject
                    InstructionStepData(
                        stepNumber = stepObj.get("stepNumber")?.takeIf { it.isJsonPrimitive }?.asInt,
                        stepName = stepObj.get("stepName")?.takeIf { it.isJsonPrimitive }?.asString,
                        durationMinutes = stepObj.get("durationMinutes")?.takeIf { it.isJsonPrimitive }?.asInt,
                        content = stepObj.get("content")?.takeIf { it.isJsonPrimitive }?.asString,
                        hiddenContent = stepObj.get("hiddenContent")?.takeIf { it.isJsonPrimitive }?.asString
                    )
                } else {
                    null
                }
            }
        } catch (e: Exception) {
            Logger.w("Failed to parse instruction steps", e)
            null
        }
    }
    
    fun getSlotData(lessonJsonData: LessonJsonData?, dayOfWeek: String?, slotNumber: Int?): SlotData? {
        if (dayOfWeek == null || slotNumber == null) {
            return null
        }
        
        val dayData = lessonJsonData?.days?.get(dayOfWeek) ?: return null
        val slotKey = slotNumber.toString()
        return dayData.slots[slotKey]
    }
    
    fun convertToLessonSteps(
        slotData: SlotData?,
        planId: String,
        dayOfWeek: String,
        slotNumber: Int
    ): List<com.bilingual.lessonplanner.domain.model.LessonStep> {
        if (slotData == null || slotData.instruction_steps.isNullOrEmpty()) {
            return emptyList()
        }
        
        return slotData.instruction_steps.mapIndexed { index, stepData ->
            com.bilingual.lessonplanner.domain.model.LessonStep(
                id = "${planId}-${dayOfWeek}-${slotNumber}-${index + 1}",
                lessonPlanId = planId,
                dayOfWeek = dayOfWeek,
                slotNumber = slotNumber,
                stepNumber = stepData.stepNumber ?: (index + 1),
                stepName = stepData.stepName ?: "Step ${index + 1}",
                durationMinutes = stepData.durationMinutes ?: 10,
                contentType = "text",
                displayContent = stepData.content ?: "",
                hiddenContent = stepData.hiddenContent,
                sentenceFrames = slotData.sentence_frames?.joinToString("\n") ?: "",
                materialsNeeded = slotData.materials_needed?.joinToString(", ") ?: "",
                vocabularyCognates = slotData.vocabulary_cognates?.joinToString("\n") ?: slotData.vocabulary?.joinToString("\n") ?: "",
                syncedAt = System.currentTimeMillis()
            )
        }
    }
}

