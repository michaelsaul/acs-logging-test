"""Count the number of each log event in a log and clear them from
the queue.

"""

import config
import notify 
from log import Log
from messageQueue import Queue
from summaryTable import SummaryTable

import json
import os
import re
import socket
import sys
import time
import traceback

global summary

class Analyzer:
  def __init__(self):
    self.log = Log()
    self.log.debug("Storage account for analyzer: {0}".format(config.AZURE_STORAGE_ACCOUNT_NAME))
    self.msgQueue = Queue(account_name = config.AZURE_STORAGE_ACCOUNT_NAME, account_key=config.AZURE_STORAGE_ACCOUNT_KEY, queue_name=config.AZURE_STORAGE_QUEUE_NAME)
    self.summary = SummaryTable(config.AZURE_STORAGE_ACCOUNT_NAME, config.AZURE_STORAGE_ACCOUNT_KEY, config.AZURE_STORAGE_SUMMARY_TABLE_NAME)
    self.keep_running = bool(config.ANALYZER_KEEP_RUNNING)
    self.log.debug("Analyzer keep running: {0}".format(self.keep_running))
    if self.keep_running:
      self.sleep_time = float(config.ANALYZER_SLEEP_TIME)
      self.log.debug("Sleep time between analyses: {0}".format(self.sleep_time))

  def incrementCount(self, event_type):
    count = self.summary.getCount(event_type)
    count = count + 1
    self.summary.updateCount(event_type, count)
    self.log.info(event_type + " count is now " + str(count))

  def processEvent(self, message):
    msg = message.message_text

    split = msg.find(" - ")
    if (not split):
      event_type = "OTHER"
    else:
      event_type = msg[:split]    
      
    # Sleep to simulated a longer running process
    time.sleep(self.sleep_time)

    self.incrementCount(event_type)

  def fullAnalysis(self):
    hostname = socket.gethostname()
    msg = hostname + ': Analyzing log event queue'
    notify.info(msg)
    while True:
      events = self.msgQueue.dequeue()
      if len(events) > 0:
        for event in events:
          self.log.info("Dequeued: " + event.message_text)
          try:
            self.processEvent(event)
            self.msgQueue.delete(event)
            self.log.info("Counted and deleted: " + event.message_text)
          except:
            e = sys.exc_info()[0]
            self.log.error("Could not process: " + event.message_text + " because %s" % e)
            traceback.print_exc(file=sys.stdout)
      else:
          break
      time.sleep(self.sleep_time)   

if __name__ == "__main__":
  analyzer = Analyzer()  
  analyzer.fullAnalysis()
