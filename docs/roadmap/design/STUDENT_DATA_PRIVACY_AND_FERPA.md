# Student Data Privacy and FERPA Compliance

## 📋 Overview
The protection of student data is a legal requirement under **FERPA (Family Educational Rights and Privacy Act)** and an ethical cornerstone of this project. This document defines the mandatory technical and procedural safeguards for handling Personally Identifiable Information (PII) within the Lesson Planner ecosystem.

## 🔐 The "No-PII-in-Cloud" Rule
The most critical safeguard in this architecture is the strict isolation of student identity from all third-party cloud services and LLMs.

1. **LLM Neutrality**: No student name, real ID, or sensitive personal detail (address, birthdate) MUST ever be sent to an LLM API (Anthropic, Google, OpenAI).
2. **Pseudonymization**: When the system requires AI to reason about a student (e.g., adaptive level selection), it MUST use a **Stable Opaque Identifier** (e.g., `student_8f2a`).
3. **Local Mapping**: The mapping between the local `student_id` and the real student name MUST reside solely on the teacher's local machine or the school's controlled server, encrypted at rest.

## 🛡️ Technical Safeguards

### 1. Data Encryption
- **Encryption at Rest**: All databases and files containing student records (`ASSESSMENT_MODULE` results, `WORKSHEET_MODULE` scans) MUST be encrypted using **AES-256**.
- **Encryption in Transit**: Any data sync between the Teacher PC and the Classroom Tablet MUST use secure, local channels (USB, Local Wi-Fi with TLS 1.3). No PII may traverse the open internet.

### 2. The "School Official" Model
Our software must be designed to function as a "School Official" under FERPA:
- **Direct Control**: The school/teacher maintains 100% control over the data.
- **No Secondary Use**: Student data MUST NEVER be used for product improvement, AI training, or advertising.
- **Audit Trails**: Every access or modification to student records MUST be logged in a tamper-resistant local audit file.

### 3. Physical-Digital Privacy (QR & FastScan)
- **Metadata Masking**: QR codes on worksheets SHOULD encode an encrypted or hashed student identifier rather than a plain text name.
- **Secure Archival**: Scanned worksheet images MUST be stored in the encrypted local store and linked to the student record via the opaque ID.

## 🤖 Agentic Privacy Rules
When AI agents perform tasks, they MUST follow these built-in constraints:

1. **Rule: Sanitization Filter**: Before sending any context to a generator, the agent MUST run a "Sanitization Pass" to replace any accidentally entered names with placeholders.
2. **Rule: Purpose Limitation**: The agent is restricted to using assessment data *only* for pedagogical adjustments (differentiation) and never for profiling or external reporting.
3. **Rule: No Trailing Memory**: Agents MUST NOT store student-specific data in their persistent "long-term memory" (Vector DB) unless it is fully anonymized.

## 📉 Data Retention & Deletion
- **"End of Year" Purge**: The system MUST provide an automated tool for teachers to purge student-level data at the end of the school year while retaining anonymized curriculum performance data for the next year.
- **Right to Erasure**: The system MUST support individual data deletion if requested by a parent or the school district.

## 📜 Compliance Checklist for Modules
- [ ] **Assessment Module**: Uses opaque UUIDs for tracking progress.
- [ ] **cmi5 Generator**: Packages contain NO PII; student level is passed via a transient launch parameter.
- [ ] **Worksheet Module**: QR codes use encrypted metadata.
- [ ] **Cloud Sync**: Only synchronizes curriculum/JSON data, never student results.
