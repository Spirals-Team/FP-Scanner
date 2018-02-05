from pymongo import MongoClient
from fingerprint import Fingerprint
from bson.objectid import ObjectId

class FingerprintDataManager:
    def __init__(self):
        self.client = MongoClient()
        self.db = self.client.usenix18
        self.collection = self.db.fingerprint

    def get_all_fingerprints(self):
        fps = self.collection.find()
        fp_objects = []
        for fingerprint in fps:
            fp_objects.append(Fingerprint(fingerprint))

        return fp_objects

    def get_fingerprints_countermeasure(self, countermeasure):
        fps = self.collection.find({'countermeasure': countermeasure})
        fp_objects = []
        for fingerprint in fps:
            fp_objects.append(Fingerprint(fingerprint))

        return fp_objects

    """
        Takes as input a mongodb id and returns the associated fingerprint
    """
    def get_fingerprint(self, fingerprint_id):
        return Fingerprint(self.collection.find({"_id": ObjectId(fingerprint_id)})[0])
