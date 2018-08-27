import time
import json
import requests

URL = "https://spaceknow-tasking.appspot.com"

class TaskInProgress:
    def __init__(self, pipelineId, status=None, headers={"content-type": "application/json"}):
        self.pipelineId = pipelineId
        self.status = status
        self.headers = headers
        if self.status is None:
            self.checkStatus()

    def checkStatus(self):
        if not hasattr(self, "pipelineId"):
            raise TypeError("Instance of class TaskInProgress has no atrribute pipelineId")
        if hasattr(self, "headers"):
            headers = self.headers
        else:
            headers = {"content-type": "application/json"}

        request = {
            "pipelineId": self.pipelineId
        }
        response = requests.post(
            URL + "/tasking/get-status",
            headers=headers,
            data=json.dumps(request))
        response_json = response.json()
        self.status = response_json["status"]
        return self.status

    def wait_till_job_is_done(self):
        if self.status in ["NEW", "PROCESSING"]:
            while True:
                self.checkStatus()
                if self.status in ["FAILED", "RESOLVED"]:
                    # not in ["NEW", "PROCESSING"]
                    break
                time.sleep(10.0)


if __name__ == '__main__':
    task = TaskInProgress("Y12G0nncqAMDPpW4ESaA")
    print(task.status)