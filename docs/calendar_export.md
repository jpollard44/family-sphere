# FamilySphere Calendar Export Feature

## Overview

The Calendar Export feature allows users to export their family calendar events to the standard iCalendar (.ics) format, which can be imported into popular calendar applications like Google Calendar, Apple Calendar, Microsoft Outlook, and others.

## Features

- Export all family calendar events to an iCalendar (.ics) file
- Include events shared with your family from other families
- Support for recurring events with various patterns (daily, weekly, biweekly, monthly, yearly)
- Proper handling of all-day events vs. timed events
- Inclusion of event details such as location, description, and categories
- Support for event organizers and attendees

## Technical Implementation

### Export Process

1. The user clicks the "Export" button in the calendar view
2. The application retrieves all events for the user's family from the database
3. It also retrieves events shared with the user's family from other families
4. The application creates a new iCalendar object and adds all events to it
5. The iCalendar file is generated and sent to the user's browser for download

### iCalendar Format

The export follows the iCalendar (RFC 5545) standard, which ensures compatibility with most calendar applications. Key components include:

- **VCALENDAR**: The main calendar component
- **VEVENT**: Individual event components
- **RRULE**: Recurrence rules for recurring events
- **DTSTART/DTEND**: Start and end times for events
- **SUMMARY/DESCRIPTION/LOCATION**: Event details

### Date and Time Handling

- All-day events use DATE values without time components
- Timed events include both date and time with timezone information
- End dates for all-day events are set to the day after the event (per iCalendar spec)
- Time zones are properly handled to ensure events appear at the correct time when imported

## User Guide

### Exporting Your Calendar

1. Navigate to the Calendar page in FamilySphere
2. Click the "Export" button in the top-right corner
3. In the export modal, click "Export Now"
4. Your browser will download an .ics file with your calendar events

### Importing into Other Calendar Applications

#### Google Calendar

1. Go to [Google Calendar](https://calendar.google.com/)
2. Click the "+" button next to "Other calendars"
3. Select "Import"
4. Choose the downloaded .ics file
5. Select the calendar to import into
6. Click "Import"

#### Apple Calendar

1. Open the Calendar app
2. Go to File > Import
3. Select the downloaded .ics file
4. Choose which calendar to add the events to
5. Click "Import"

#### Microsoft Outlook

1. Open Outlook
2. Go to File > Open & Export > Import/Export
3. Select "Import an iCalendar (.ics) or vCalendar file (.vcs)"
4. Browse to the downloaded .ics file
5. Choose to import as a new calendar or into an existing calendar

## Limitations and Future Improvements

- Currently, the export does not include event attachments
- Reminder settings are not included in the export
- Future versions will add support for selective export (date range, specific events)
- Calendar subscription functionality (live updates) is planned for a future release
