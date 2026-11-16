const API = "/api";

async function apiRequest(path, options = {}) {
    const response = await fetch(`${API}${path}`, {
        headers: { "Content-Type": "application/json", ...(options.headers || {}) },
        ...options
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.message || "Request failed.");
    return data;
}

function cell(row, value) {
    const td = document.createElement("td");
    td.textContent = value ?? "";
    row.appendChild(td);
    return td;
}

function actionCell(row, editFn, deleteFn) {
    const td = document.createElement("td");
    const edit = document.createElement("button");
    edit.className = "edit-btn";
    edit.textContent = "Edit";
    edit.addEventListener("click", () => editFn(row));
    const del = document.createElement("button");
    del.className = "delete-btn";
    del.textContent = "Delete";
    del.addEventListener("click", () => deleteFn(row));
    td.append(edit, del);
    row.appendChild(td);
}

function makeRow(tbody, id, values, editFn, deleteFn) {
    const tr = document.createElement("tr");
    tr.dataset.id = id;
    values.forEach(value => cell(tr, value));
    actionCell(tr, editFn, deleteFn);
    tbody.appendChild(tr);
    return tr;
}

function setCount(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
}

function showForm(id) {
    const form = document.getElementById(id);
    if (form) form.style.display = "block";
}

function closeForm(id) {
    const form = document.getElementById(id);
    if (form) form.style.display = "none";
}

function val(id) {
    return document.getElementById(id).value.trim();
}

function clearFields(ids) {
    ids.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = "";
    });
}

function showError(error) {
    alert(error.message || "Something went wrong.");
}

// ---------------- STUDENTS ----------------
function showStudentForm() { showForm("studentForm"); }
function showFormCompat() { showStudentForm(); }

async function addStudent() {
    const data = {
        full_name: val("studentName"),
        roll_number: val("rollNumber"),
        room_number: val("roomNumber"),
        department: val("department"),
        contact_number: val("contact"),
        guardian_contact: val("guardianContact"),
        email: val("studentEmail"),
        gender: val("studentGender"),
        address: val("studentAddress")
    };
    try {
        await apiRequest("/students", { method: "POST", body: JSON.stringify(data) });
        clearFields(["studentName","rollNumber","roomNumber","department","contact","guardianContact","studentEmail","studentGender","studentAddress"]);
        closeForm("studentForm");
        await loadStudents();
        alert("Student added successfully!");
    } catch (e) { showError(e); }
}

async function loadStudents() {
    try {
        const students = await apiRequest("/students");
        const tbody = document.getElementById("studentTableBody");
        tbody.innerHTML = "";
        students.forEach(s => makeRow(tbody, s.student_id,
            [s.full_name, s.roll_number, s.room_number || "-", s.contact_number, s.status],
            editStudent, deleteStudent));
        setCount("totalStudents", students.length);
        updateDashboard();
    } catch (e) { showError(e); }
}

async function editStudent(row) {
    const id = row.dataset.id;
    const name = prompt("Enter Student Name:", row.cells[0].textContent);
    if (name === null || !name.trim()) return;
    const roll = prompt("Enter Roll Number:", row.cells[1].textContent);
    if (roll === null || !roll.trim()) return;
    const room = prompt("Enter Room Number (leave blank if none):", row.cells[2].textContent === "-" ? "" : row.cells[2].textContent);
    if (room === null) return;
    const contact = prompt("Enter Contact Number (11 digits):", row.cells[3].textContent);
    if (contact === null || !/^\d{11}$/.test(contact.trim())) return alert("Contact number must be 11 digits.");
    try {
        await apiRequest(`/students/${id}`, { method: "PUT", body: JSON.stringify({
            full_name: name.trim(), roll_number: roll.trim(), room_number: room.trim(), contact_number: contact.trim()
        })});
        await loadStudents();
        alert("Student updated successfully!");
    } catch (e) { showError(e); }
}

async function deleteStudent(row) {
    if (!confirm("Are you sure you want to delete this student?")) return;
    try {
        await apiRequest(`/students/${row.dataset.id}`, { method: "DELETE" });
        await loadAll();
        alert("Student deleted successfully!");
    } catch (e) { showError(e); }
}

function searchStudent() { searchRows("studentTableBody", [0,1]); }

// ---------------- ROOMS ----------------
function showRoomForm() { showForm("roomForm"); }

async function addRoom() {
    const data = { room_number: val("roomNo"), capacity: Number(val("roomCapacity")), occupied_beds: Number(val("occupiedBeds") || 0) };
    try {
        await apiRequest("/rooms", { method: "POST", body: JSON.stringify(data) });
        clearFields(["roomNo","roomCapacity"]); document.getElementById("occupiedBeds").value = "0";
        closeForm("roomForm"); await loadAll(); alert("Room added successfully!");
    } catch (e) { showError(e); }
}

async function loadRooms() {
    const rooms = await apiRequest("/rooms");
    const tbody = document.getElementById("roomTableBody"); tbody.innerHTML = "";
    rooms.forEach(r => {
        const available = r.capacity - r.occupied_beds;
        makeRow(tbody, r.room_id, [r.room_number,r.capacity,r.occupied_beds,available,available > 0 ? "Available" : "Full"], editRoom, deleteRoom);
    });
    updateDashboard();
}

async function editRoom(row) {
    const room_number = prompt("Room Number:", row.cells[0].textContent); if (room_number === null || !room_number.trim()) return;
    const capacity = Number(prompt("Room Capacity:", row.cells[1].textContent)); if (!capacity) return;
    const occupied_beds = Number(prompt("Occupied Beds:", row.cells[2].textContent)); if (!Number.isInteger(occupied_beds) || occupied_beds < 0 || occupied_beds > capacity) return alert("Invalid occupied beds.");
    try { await apiRequest(`/rooms/${row.dataset.id}`, {method:"PUT",body:JSON.stringify({room_number:room_number.trim(),capacity,occupied_beds})}); await loadAll(); alert("Room updated!"); }
    catch(e) { showError(e); }
}
async function deleteRoom(row) {
    if (!confirm("Delete this room?")) return;
    try { await apiRequest(`/rooms/${row.dataset.id}`,{method:"DELETE"}); await loadAll(); alert("Room deleted!"); }
    catch(e) { showError(e); }
}
function searchRoom() { searchRows("roomTableBody",[0]); }

// ---------------- FEES ----------------
function showFeeForm() { showForm("feeForm"); }
async function addFee() {
    const data = {student_name:val("feeStudentName"),roll_number:val("feeRollNumber"),amount:Number(val("feeAmount")),fee_month:val("feeMonth"),status:val("feeStatus")};
    try {
        await apiRequest("/fees",{method:"POST",body:JSON.stringify(data)});
        clearFields(["feeStudentName","feeRollNumber","feeAmount","feeMonth"]); closeForm("feeForm");
        await loadAll(); alert("Fee added successfully!");
    } catch(e) { showError(e); }
}
async function loadFees() {
    const fees = await apiRequest("/fees"); const tbody = document.getElementById("feeTableBody"); tbody.innerHTML = "";
    fees.forEach(f => makeRow(tbody,f.fee_id,[f.student_name,f.roll_number,f.amount,f.fee_month,f.status],editFee,deleteFee));
    updateDashboard();
}
async function editFee(row) {
    const student_name=prompt("Student Name:",row.cells[0].textContent); if(student_name===null||!student_name.trim())return;
    const roll_number=prompt("Roll Number:",row.cells[1].textContent); if(roll_number===null||!roll_number.trim())return;
    const amount=Number(prompt("Fee Amount:",row.cells[2].textContent)); if(!amount||amount<0)return alert("Enter a valid amount.");
    const fee_month=prompt("Month:",row.cells[3].textContent); if(fee_month===null||!fee_month.trim())return;
    const status=prompt("Status (Paid/Unpaid):",row.cells[4].textContent); if(!["Paid","Unpaid"].includes(status))return alert("Status must be Paid or Unpaid.");
    try { await apiRequest(`/fees/${row.dataset.id}`,{method:"PUT",body:JSON.stringify({student_name,roll_number,amount,fee_month,status})}); await loadAll(); alert("Fee updated!"); }
    catch(e){showError(e);}
}
async function deleteFee(row) {
    if(!confirm("Delete this fee record?"))return;
    try{await apiRequest(`/fees/${row.dataset.id}`,{method:"DELETE"});await loadAll();alert("Fee deleted!");}catch(e){showError(e);}
}
function searchFee(){searchRows("feeTableBody",[0,1]);}

// ---------------- ATTENDANCE ----------------
function showAttendanceForm(){showForm("attendanceForm");}
async function addAttendance(){
    const data={student_name:val("attendanceName"),roll_number:val("attendanceRoll"),attendance_date:val("attendanceDate"),status:val("attendanceStatus")};
    try{await apiRequest("/attendance",{method:"POST",body:JSON.stringify(data)});clearFields(["attendanceName","attendanceRoll","attendanceDate"]);closeForm("attendanceForm");await loadAll();alert("Attendance saved!");}
    catch(e){showError(e);}
}
async function loadAttendance(){
    const records=await apiRequest("/attendance");const tbody=document.getElementById("attendanceTableBody");tbody.innerHTML="";
    records.forEach(a=>makeRow(tbody,a.attendance_id,[a.student_name,a.roll_number,a.attendance_date,a.status],editAttendance,deleteAttendance));
    const present=records.filter(a=>a.status==="Present").length, absent=records.filter(a=>a.status==="Absent").length;
    setCount("totalPresent",present);setCount("totalAbsent",absent);updateDashboard();
}
async function editAttendance(row){
    const student_name=prompt("Student Name:",row.cells[0].textContent);if(student_name===null||!student_name.trim())return;
    const roll_number=prompt("Roll Number:",row.cells[1].textContent);if(roll_number===null||!roll_number.trim())return;
    const attendance_date=prompt("Date (YYYY-MM-DD):",row.cells[2].textContent);if(attendance_date===null||!attendance_date.trim())return;
    const status=prompt("Status (Present/Absent):",row.cells[3].textContent);if(!["Present","Absent"].includes(status))return alert("Invalid status.");
    try{await apiRequest(`/attendance/${row.dataset.id}`,{method:"PUT",body:JSON.stringify({student_name,roll_number,attendance_date,status})});await loadAll();alert("Attendance updated!");}
    catch(e){showError(e);}
}
async function deleteAttendance(row){
    if(!confirm("Delete this attendance record?"))return;
    try{await apiRequest(`/attendance/${row.dataset.id}`,{method:"DELETE"});await loadAll();alert("Attendance deleted!");}catch(e){showError(e);}
}
function searchAttendance(){searchRows("attendanceTableBody",[0,1]);}

// ---------------- COMPLAINTS ----------------
function showComplaintForm(){showForm("complaintForm");}
async function addComplaint(){
    const data={student_name:val("complaintName"),roll_number:val("complaintRoll"),category:"Other",subject:"Admin entered complaint",details:val("complaintDescription")};
    try{await apiRequest("/complaints",{method:"POST",body:JSON.stringify(data)});clearFields(["complaintName","complaintRoll","complaintDescription","complaintDate"]);closeForm("complaintForm");await loadAll();alert("Complaint added!");}
    catch(e){showError(e);}
}
async function loadComplaints(){
    const complaints=await apiRequest("/complaints");const tbody=document.getElementById("complaintTableBody");tbody.innerHTML="";
    complaints.forEach(c=>{
        const row=makeRow(tbody,c.complaint_id,
            [c.student_name||"",c.roll_number||"",`${c.category}: ${c.subject} — ${c.details}`,c.complaint_date||"",c.status],
            editComplaint,deleteComplaint);
        row.dataset.category=c.category||"Other";
        row.dataset.subject=c.subject||"";
        row.dataset.details=c.details||"";
    });
    updateDashboard();
}
async function editComplaint(row){
    const student_name=prompt("Student Name:",row.cells[0].textContent);if(student_name===null)return;
    const roll_number=prompt("Roll Number:",row.cells[1].textContent);if(roll_number===null)return;
    const category=prompt("Category:",row.dataset.category||"Other");if(category===null||!category.trim())return;
    const subject=prompt("Subject:",row.dataset.subject||"");if(subject===null||!subject.trim())return;
    const details=prompt("Complaint Details:",row.dataset.details||"");if(details===null||!details.trim())return;
    const status=prompt("Status (Pending/Resolved):",row.cells[4].textContent);if(!["Pending","Resolved"].includes(status))return alert("Invalid status.");
    try{await apiRequest(`/complaints/${row.dataset.id}`,{method:"PUT",body:JSON.stringify({student_name,roll_number,category,subject,details,status})});await loadAll();alert("Complaint updated!");}
    catch(e){showError(e);}
}
async function deleteComplaint(row){
    if(!confirm("Delete this complaint?"))return;
    try{await apiRequest(`/complaints/${row.dataset.id}`,{method:"DELETE"});await loadAll();alert("Complaint deleted!");}catch(e){showError(e);}
}
function searchComplaint(){searchRows("complaintTableBody",[0,1]);}

// ---------------- DASHBOARD / SEARCH / LOGIN ----------------
function searchRows(tbodyId, indexes){
    const term=(document.querySelector(`#${tbodyId.replace("TableBody","")}`)?.value||"").toLowerCase();
    const tbody=document.getElementById(tbodyId);
    if(!tbody)return;
    [...tbody.rows].forEach(row=>{
        const text=indexes.map(i=>row.cells[i]?.textContent.toLowerCase()||"").join(" ");
        row.style.display=text.includes(term)?"":"none";
    });
}
// Use the actual search input IDs, whose names match the table section.
function filterTable(inputId, tbodyId, indexes){
    const term=document.getElementById(inputId).value.toLowerCase();
    [...document.getElementById(tbodyId).rows].forEach(row=>{
        row.style.display=indexes.some(i=>row.cells[i]?.textContent.toLowerCase().includes(term))?"":"none";
    });
}
searchStudent = function(){filterTable("searchStudent","studentTableBody",[0,1]);};
searchRoom = function(){filterTable("searchRoom","roomTableBody",[0]);};
searchFee = function(){filterTable("searchFee","feeTableBody",[0,1]);};
searchAttendance = function(){filterTable("searchAttendance","attendanceTableBody",[0,1]);};
searchComplaint = function(){filterTable("searchComplaint","complaintTableBody",[0,1]);};

function updateDashboard(){
    const students=document.querySelectorAll("#studentTableBody tr").length;
    const rooms=[...document.querySelectorAll("#roomTableBody tr")];
    const available=rooms.filter(r=>r.cells[4]?.textContent==="Available").length;
    const fees=[...document.querySelectorAll("#feeTableBody tr")];
    const total=fees.filter(r=>r.cells[4]?.textContent==="Paid").reduce((sum,r)=>sum+Number(r.cells[2].textContent||0),0);
    const present=[...document.querySelectorAll("#attendanceTableBody tr")].filter(r=>r.cells[3]?.textContent==="Present").length;
    const complaints=[...document.querySelectorAll("#complaintTableBody tr")];
    const pending=complaints.filter(r=>r.cells[4]?.textContent==="Pending").length;
    setCount("totalStudents",students);setCount("totalRooms",rooms.length);setCount("availableRooms",available);
    setCount("totalFee",`Rs. ${total}`);setCount("dashboardPresent",present);
    setCount("totalComplaints",complaints.length);setCount("pendingComplaints",pending);
}

async function loadAll(){
    try{
        await Promise.all([loadStudents(),loadRooms(),loadFees(),loadAttendance(),loadComplaints()]);
        updateDashboard();
    }catch(e){showError(e);}
}

function handleLogin(event){
    event.preventDefault();
    const username=val("loginUsername"),password=document.getElementById("loginPassword").value;
    if(username==="admin"&&password==="12345"){
        document.getElementById("loginScreen").style.display="none";
        document.getElementById("loginError").textContent="";
        document.getElementById("loginForm").reset();
    }else{
        document.getElementById("loginError").textContent="Incorrect Username or Password!";
    }
}
function logoutUser(){
    if(confirm("Are you sure you want to logout?")){
        document.getElementById("loginScreen").style.display="flex";
        document.getElementById("loginForm").reset();
        document.getElementById("loginError").textContent="";
    }
}
function togglePassword(){
    const field=document.getElementById("loginPassword"),button=document.querySelector(".show-password");
    field.type=field.type==="password"?"text":"password";
    button.textContent=field.type==="password"?"Show":"Hide";
}

document.addEventListener("DOMContentLoaded",loadAll);

async function loadPendingStudents() {
    const tbody = document.getElementById("pendingStudentTableBody");
    if (!tbody) return;

    try {
        const response = await fetch("/api/students/pending");
        const students = await response.json();

        tbody.innerHTML = "";

        if (!response.ok) {
            throw new Error(students.message || "Could not load registrations.");
        }

        if (students.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6">No Pending Registrations Found</td>
                </tr>`;
            return;
        }

        students.forEach(student => {
            const row = document.createElement("tr");

            const values = [
                student.full_name,
                student.roll_number,
                student.department,
                student.contact_number,
                student.email
            ];

            values.forEach(value => {
                const cell = document.createElement("td");
                cell.textContent = value || "";
                row.appendChild(cell);
            });

            const actionCell = document.createElement("td");

            const approveBtn = document.createElement("button");
            approveBtn.textContent = "Approve";
            approveBtn.onclick = () => approveStudent(student.student_id);

            const rejectBtn = document.createElement("button");
            rejectBtn.textContent = "Reject";
            rejectBtn.onclick = () => rejectStudent(student.student_id);

            actionCell.appendChild(approveBtn);
            actionCell.appendChild(rejectBtn);
            row.appendChild(actionCell);

            tbody.appendChild(row);
        });

    } catch (error) {
        tbody.innerHTML = `
            <tr><td colspan="6">${error.message}</td></tr>`;
    }
}

async function updateStudentApproval(studentId, status) {
    try {
        const response = await fetch(`/api/students/${studentId}/approval`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ status: status })
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.message || "Action failed.");
        }

        alert(result.message);
        await loadPendingStudents();

        if (typeof loadStudents === "function") {
            await loadStudents();
        }

        if (typeof loadAll === "function") {
            await loadAll();
        }

    } catch (error) {
        alert(error.message);
    }
}

function approveStudent(studentId) {
    if (confirm("Are you sure you want to approve this student?")) {
        updateStudentApproval(studentId, "Active");
    }
}

function rejectStudent(studentId) {
    if (confirm("Are you sure you want to reject this student?")) {
        updateStudentApproval(studentId, "Rejected");
    }
}

document.addEventListener("DOMContentLoaded", loadPendingStudents);
