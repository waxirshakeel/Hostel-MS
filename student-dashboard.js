
// Common helper: Read API response
async function getAPIData(url) {
    const response = await fetch(url);
    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.message || "Something went wrong.");
    }

    return data;
}


// Common helper: Create a table
function createTable(container, columns, rows) {
    container.replaceChildren();

    if (!Array.isArray(rows) || rows.length === 0) {
        container.textContent = "No records found.";
        return;
    }

    const table = document.createElement("table");
    const headerRow = document.createElement("tr");

    columns.forEach(column => {
        const th = document.createElement("th");
        th.textContent = column.label;
        headerRow.appendChild(th);
    });

    table.appendChild(headerRow);

    rows.forEach(item => {
        const row = document.createElement("tr");

        columns.forEach(column => {
            const td = document.createElement("td");
            const value = item[column.key];

            td.textContent = value === null || value === undefined || value === ""
                ? "Not Available"
                : String(value);

            row.appendChild(td);
        });

        table.appendChild(row);
    });

    container.appendChild(table);
}


// Get array from API response
function getRows(data, possibleKeys) {
    if (Array.isArray(data)) {
        return data;
    }

    for (const key of possibleKeys) {
        if (Array.isArray(data[key])) {
            return data[key];
        }
    }

    return [];
}


// Load Student Dashboard
async function loadStudentDashboard() {
    const welcome = document.getElementById("studentWelcome");

    try {
        const student = await getAPIData("/api/student/me");
        welcome.textContent = "Welcome, " + student.full_name + "!";
    } catch (error) {
        window.location.href = "/student-login";
    }
}


// Show one section and hide the others
function showStudentSection(sectionId) {
    const sectionIds = [
        "myProfileSection",
        "myRoomSection",
        "myFeesSection",
        "paymentHistorySection",
        "myAttendanceSection",
        "myComplaintsSection"
    ];

    document.getElementById("studentDashboardMenu").style.display = "none";

    sectionIds.forEach(id => {
        document.getElementById(id).style.display = "none";
    });

    document.getElementById(sectionId).style.display = "block";
    document.getElementById(sectionId).scrollIntoView({
        behavior: "smooth"
    });
}


// Back to Dashboard
function backToDashboard() {
    const sectionIds = [
        "myProfileSection",
        "myRoomSection",
        "myFeesSection",
        "paymentHistorySection",
        "myAttendanceSection",
        "myComplaintsSection"
    ];

    sectionIds.forEach(id => {
        document.getElementById(id).style.display = "none";
    });

    document.getElementById("studentDashboardMenu").style.display = "grid";

    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}


// Load My Profile
async function loadMyProfile() {
    showStudentSection("myProfileSection");

    const container = document.getElementById("profileDetails");
    container.textContent = "Loading Profile...";

    try {
        const student = await getAPIData("/api/student/me");

        const details = [
            ["Full Name", student.full_name],
            ["Roll Number", student.roll_number],
            ["Email Address", student.email],
            ["Department", student.department],
            ["Contact Number", student.contact_number],
            ["Guardian Contact", student.guardian_contact],
            ["Gender", student.gender],
            ["Address", student.address],
            ["Room Number", student.room_number],
            ["Account Status", student.status]
        ];

        const table = document.createElement("table");

        details.forEach(([label, value]) => {
            const row = document.createElement("tr");
            const th = document.createElement("th");
            const td = document.createElement("td");

            th.textContent = label;
            td.textContent = value || "Not Available";

            row.appendChild(th);
            row.appendChild(td);
            table.appendChild(row);
        });

        container.replaceChildren(table);

    } catch (error) {
        container.textContent = error.message;
    }
}


// Load My Room
async function loadMyRoom() {
    showStudentSection("myRoomSection");

    const container = document.getElementById("roomDetails");
    container.textContent = "Loading Room Details...";

    try {
        const room = await getAPIData("/api/student/room");

        const details = [
            ["Room ID", room.room_id],
            ["Room Number", room.room_number],
            ["Room Capacity", room.capacity],
            ["Occupied Beds", room.occupied_beds],
            ["Available Beds", room.capacity - room.occupied_beds]
        ];

        const table = document.createElement("table");

        details.forEach(([label, value]) => {
            const row = document.createElement("tr");
            const th = document.createElement("th");
            const td = document.createElement("td");

            th.textContent = label;
            td.textContent = value ?? "Not Available";

            row.appendChild(th);
            row.appendChild(td);
            table.appendChild(row);
        });

        container.replaceChildren(table);

    } catch (error) {
        container.textContent = error.message;
    }
}


// Load My Fees
async function loadMyFees() {
    showStudentSection("myFeesSection");

    const container = document.getElementById("feesDetails");
    container.textContent = "Loading Fee Details...";

    try {
        const data = await getAPIData("/api/student/fees");
        const fees = getRows(data, ["fees", "records"]);

        createTable(container, [
            { key: "fee_month", label: "Fee Month" },
            { key: "amount", label: "Amount" },
            { key: "status", label: "Payment Status" }
        ], fees);

    } catch (error) {
        container.textContent = error.message;
    }
}


// Load Payment History
async function loadPaymentHistory() {
    showStudentSection("paymentHistorySection");

    const container = document.getElementById("paymentHistoryDetails");
    container.textContent = "Loading Payment History...";

    try {
        const data = await getAPIData("/api/student/payment-history");
        const payments = getRows(data, ["payments", "history", "records"]);

        createTable(container, [
            { key: "fee_month", label: "Fee Month" },
            { key: "amount", label: "Amount Paid" },
            { key: "status", label: "Status" },
            { key: "created_at", label: "Payment Date" }
        ], payments);

    } catch (error) {
        container.textContent = error.message;
    }
}


// Load Attendance
async function loadMyAttendance() {
    showStudentSection("myAttendanceSection");

    const container = document.getElementById("attendanceDetails");
    container.textContent = "Loading Attendance...";

    try {
        const data = await getAPIData("/api/student/attendance");
        const attendance = getRows(data, ["attendance", "records"]);

        createTable(container, [
            { key: "attendance_date", label: "Date" },
            { key: "status", label: "Attendance Status" }
        ], attendance);

    } catch (error) {
        container.textContent = error.message;
    }
}


// Load Complaints
async function loadMyComplaints() {
    showStudentSection("myComplaintsSection");

    document.getElementById("complaintMessage").textContent = "";

    const container = document.getElementById("complaintsDetails");
    container.textContent = "Loading Complaints...";

    try {
        const data = await getAPIData("/api/student/complaints");
        const complaints = getRows(data, ["complaints", "records"]);

        createTable(container, [
            { key: "category", label: "Category" },
            { key: "subject", label: "Subject" },
            { key: "details", label: "Details" },
            { key: "status", label: "Status" },
            { key: "complaint_date", label: "Date" }
        ], complaints);

    } catch (error) {
        container.textContent = error.message;
    }
}


// Submit New Complaint
document.getElementById("complaintForm").addEventListener("submit", async function(event) {
    event.preventDefault();

    const message = document.getElementById("complaintMessage");
    const submitButton = this.querySelector('button[type="submit"]');

    const complaint = {
        category: document.getElementById("complaintCategory").value,
        subject: document.getElementById("complaintSubject").value.trim(),
        details: document.getElementById("complaintDetails").value.trim()
    };

    if (!complaint.category || !complaint.subject || !complaint.details) {
        message.textContent = "Please fill in all complaint fields.";
        return;
    }

    submitButton.disabled = true;
    message.textContent = "Submitting your complaint...";

    try {
        const response = await fetch("/api/student/complaints", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(complaint)
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.message || "Unable to submit complaint.");
        }

        message.textContent = result.message || "Complaint submitted successfully!";

        this.reset();

        await loadComplaintsListOnly();

    } catch (error) {
        message.textContent = error.message;
    } finally {
        submitButton.disabled = false;
    }
});


// Refresh complaints list after submission
async function loadComplaintsListOnly() {
    const container = document.getElementById("complaintsDetails");
    container.textContent = "Loading Complaints...";

    try {
        const data = await getAPIData("/api/student/complaints");
        const complaints = getRows(data, ["complaints", "records"]);

        createTable(container, [
            { key: "category", label: "Category" },
            { key: "subject", label: "Subject" },
            { key: "details", label: "Details" },
            { key: "status", label: "Status" },
            { key: "complaint_date", label: "Date" }
        ], complaints);

    } catch (error) {
        container.textContent = error.message;
    }
}


// Student Logout
async function studentLogout() {
    try {
        await fetch("/api/student-logout", {
            method: "POST"
        });

        window.location.href = "/student-login";

    } catch (error) {
        alert("Logout failed. Please try again.");
    }
}


// Start Dashboard
document.addEventListener("DOMContentLoaded", loadStudentDashboard);
