# Real-time, scheduled, and on-demand reporting
A case study on when and why I choose to make certain reports. 

## The problem
Retail locations need to be as informed and agile as possible so they know when and how to make decisions. How do you make informed decisions about operational efficiency, product popularity, or labor allocation? Data. How do you contextualize this data when it comes from various sources, different departments need different information, and not all stakeholders have the same direct access to the data (or know how to access it even if they do)? 

## A solution
Powered by Python, PHP, SQL, and cloud computing (GCP), I tailor-make reporting systems which deliver reports in real-time, on a schedule, or on-demand depending on the needs of the stakeholders. 

## Missed call reporting tool (real-time reporting)
When a retail location was getting customer complaints about waiting on the line for upwards of ten minutes but store staff and footage confirm that the phones weren’t ringing during that period, some eyebrows get raised. What initially started as a tool to report on network health by creating notifications about missed calls as they happened, quickly grew to be useful to non-technical users. 

How do you know if your opener never shows up? How do you identify staff shortages causing customers to hang up the phone? This tool proved to be quite effective. 

The VoIP platform has prebuilt reporting tools that allow for scheduled daily reporting on missed calls. But this information is already stale a day later. While day-old data can be helpful in some use cases, seeing that the opening crew didn’t show up until 1pm YESTERDAY doesn’t allow someone to be proactive about handling issues. That is why this had to be built, to create that real-time, actionable connection. 

### Implementation
This system is a series of python files (and a config file) running via systemd, cron execution, or called by their counterparts. Hosted on a VM on GCP. 

Deployed according to current Python standards with a venv instance of python3 to install modules. 

**Config**: A config file which stores global variables to inform the flow and thresholds of this software<br/>
**Database**: A helper file which handles all database connection and methods related to database interactions
**Emailer**: A helper file which handles all the actions associated with sending email notifications. 
**Listener**: A systemd python process that listens to a websocket feed delivered by VoIP server.
* **Notable packages used**: socket, threading, re
* Listener examines every call as it terminates on the server and assesses if it was not answered.  
* If call is missed, it pushed select information to a MariaDB/MySQL via Database module
* Repeat forever!
**Watcher**: Running every (x) minutes via cron, the watcher examines the database for any missed calls that were not previously reported on.
* If calls exceed limits set in config for various departments reporting requirements, an email report is created and sent to the people responsible for that store/department. 
* The config sets over which period of time are calls checked (default being the previous hour) and how many calls need to be missed over that period before a report is generated. 
* Once calls have been reported on, they are marked as such in the database so that they do not create multiple reports for the same calls. 

### Outcomes
This tool runs around the clock, watching over roughly 100,000 calls a month. It has given the business confidence, and helped catch issues as they arise rather than well after the damage is done. 

## Large online order notification (real-time reporting)
Many restaurants accept online orders for a time in the future. This feature is highly beneficial for many establishments. What do you do when someone places a $600 order due 30 minutes after opening, at a location that was projected to do $1500 in business for the entire day? You have to let them know as soon as possible! 

The online ordering platform had order notifications, but it was all or nothing, no way to differentiate between when the order was placed or how large it was. It was either send an email for all orders, or wait until the POS sent the order to the kitchen to inform staff. My clients didn’t need to know about the $20 orders beforehand, they needed to know about the $600 ones so they could make staffing and production decisions as soon as possible. 

### Implementation
PHP/Apache2 webhook endpoint accepting order details from Online order providers. No need for systemd process, let Apache2 do what it is good at and receive web requests. Hosted on GCP VM

**Config**: A config file which contains variables for dollar amount, establishment, and timing thresholds<br/>
**Emailer**: A helper file which handles email actions for notification<br/>
**Webhook endpoint**: A PHP script that interprets all online orders as they are sent in 
* Get order from provider 
* Determine if order is placed outside of business hours (set in config)
* Determine if order was above certain cost (set in config)
* If yes, send notification to the store employees, the DM, and anyone else who needs to know about it. 

### Outcomes
With this tool in place, frontline staff can be confident that they will be prepared when large order come through for time in the future. This tool has sent notifications for over $50,000 in orders since it was deployed, most of the time allowing sr. managers to get more people or products in the store so they could make happy customers. 

## Products sold report (scheduled and on-demand)
There are several datasets where real-time feeds are not helpful. Enter scheduled and on-demand reporting. My clients didn’t need to know every time an order of breadsticks was placed the moment it was placed. They needed to know how many breadsticks were ordered over a period of time. 

POS contains reports, but not in the form that operations want the data, and not organized in the markets they want to see. POS reporting is configurable but feels clunky and non-technical users struggle to use them. Tailor made to their specific needs, in the format they want means that the data is meaningfully considered.  

### Implementation
Python, PHP, POS API, and Google’s Sheets & Drive APIs, hosted on GCP VM. 

**Config**: Config file that contains important variables<br/>
**Emailer**: A helper file which handles email actions<br/>
**Database**: A helper file which handles database interactions<br/> 
**Google Drive/Sheets** A helper file that handles Google Drive & Sheets actions<br/>
**Report Builder**: Pull data from POS API to compile report
* Get data from POS for products sold over the period, per establishment
* Get establishment data, like country and parent company from database
* Compile data into spreadsheet, outlining how products are sold in various markets 
* Send spreadsheet to operations team to evaluate priorities

All of this functions on a job system. Jobs are created and placed in a database table. Jobs are pre-populated for the periods and days the operations team wants them. Custom jobs can be requested via a PHP frontend page, which is a simple form that places data in the jobs table. 

### Outcomes 
Product performance at the finger tips of the people who need to know it, delivered to their inbox every Monday morning. Can’t get much better than that. 
