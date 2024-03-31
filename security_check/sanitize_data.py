from pymongo.collection import ReturnDocument  
  
# When updating an entry in MongoDB, sanitize the input data  
def update_entry(patient_id, new_data):  
    sanitized_data = {key: sanitize(value) for key, value in new_data.items() if value}  
    result = collection.find_one_and_update(  
        {"patient_id": patient_id},  
        {"$set": sanitized_data},  
        return_document=ReturnDocument.AFTER  
    )  
    return result  
