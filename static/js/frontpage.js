function loadXLSX(callback) {
  const script = document.createElement("script");
  script.src = "../static/js/xlsx.full.min.js";
  script.onload = callback;
  document.head.appendChild(script);
}

loadXLSX(() => {
  console.log("XLSX library loaded!");
  console.log(window.XLSX);
});

let courseInfos = [];
let classInfos = [];
let inputCourseCodes = [];
let inputClassCodes = [];
let couresCreditDictionary = {};
let courseTypeDictionary = {};

let currentCourseIndex = 0;
let currentClassIndex = 0;
let totalCredits = 0;
let timetable = null;
const hiddenCourseInput = document.getElementById('course-codes');
const hiddenClassInput = document.getElementById('class-codes');

const classInput = document.getElementById('class-code-input');
const courseInput = document.getElementById('course-code-input');
const autoCompleteCourseList = document.getElementById('autocomplete-list-course');
const autoCompleteClassList = document.getElementById('autocomplete-list-class');
const fileUpload = document.getElementById('file-upload');
const fileStatus = document.getElementById('file-upload-text');
const courseTagsContainer = document.getElementById('course-tags-container');
const classTagsContainer = document.getElementById('class-tags-container');
const earliestHourInput = document.getElementById('earliest-class-hour-input');
const earliestHourSelection = document.getElementById('earliest-class-hour-list');
const creditCounter = document.getElementById('total-credits');
const earliestHourOptions = [
  "06:45",
  "07:00",
  "08:25",
  "09:20",
  "10:15",
  "14:00",
  "14:10",
  "15:05",
  "15:50",
  "16:30",
  "17:30"
];
const latestHourOptions = [
  "06:45",
  "07:00",
  "08:25",
  "09:20",
  "10:15",
  "14:00",
  "14:10",
  "15:05",
  "15:50",
  "16:30",
  "17:30"
];
function populateDropdown(listId, options) {
  const dropdown = document.getElementById(listId);
  dropdown.innerHTML = ""; // Clear existing options
  options.forEach((option) => {
    const item = document.createElement("div");
    item.classList.add("dropdown-item");
    item.textContent = option;
    item.onclick = () => selectItem(listId.replace('-list', '-input'), item);
    dropdown.appendChild(item);
  });
}
function selectItem(inputId, element) {
  const inputField = document.getElementById(inputId);
  inputField.value = element.textContent; // Set input value to selected item
  const dropdown = document.getElementById(inputId.replace('-input', '-list'));
  dropdown.style.display = "none"; // Hide dropdown
}
function showDropdown(listId) {
  const dropdown = document.getElementById(listId);
  dropdown.style.display = "block";

  // Close dropdown when clicking outside
  document.addEventListener("click", function handleClickOutside(event) {
    if (!dropdown.contains(event.target) && event.target.id !== listId.replace('-list', '-input')) {
      dropdown.style.display = "none";
      document.removeEventListener("click", handleClickOutside);
    }
  });
}
fileUpload.addEventListener('change', 
  function (event) {
    const file = event.target.files[0];
    if (file) {
      console.log("Reading");
      const reader = new FileReader();
      reader.onload = function(e) {
        const data = new Uint8Array(e.target.result);
        const workbook = window.XLSX.read(data, { type: 'array' });
        const sheet = workbook.Sheets[workbook.SheetNames[0]];
        let sheetData = window.XLSX.utils.sheet_to_json(sheet, { header: 1 });
        sheetData = sheetData.slice(2);
        timetable = sheetData
        // column 5 is the place for course code 
        // classInfos = [...new Set(sheetData.map(row => row[2] + " - " + row[5] + " - " + row[21]).filter(Boolean))];
        courseInfos = [...new Set(sheetData.map(row => row[4] + " - " + row[5]).filter(Boolean))];
        timetable.forEach(row => {
          let courseCode = row[4];
          let credits = row[7];
          if (courseCode && credits) {
            couresCreditDictionary[courseCode] = Number(credits[0]);
          }
        })
        fileStatus.textContent = `Đã tải lên tệp: ${file.name}`;
      };
      reader.readAsArrayBuffer(file);
    }
  });

classInput.addEventListener('input', function() {
  const query = classInput.value.trim().toUpperCase();
  autoCompleteClassList.innerHTML = ''; 
  const filteredClasses = classInfos.filter(classCode => classCode.startsWith(query));
  currentClassIndex = -1; 
  filteredClasses.forEach(classInfo => {
    const item = document.createElement('div');
    item.textContent = classInfo;
    var classInfoList = classInfo.split('-')
    var classCode = classInfoList[0].trim();
    var courseCode = classInfoList[1].trim();
    var classType = classInfoList[2].trim();
    item.classList.add('autocomplete-item-class');
    item.addEventListener('click', function () {
      addClass(classInfo, classCode, courseCode, classType);
      // console.log(courseCodeName, courseCode);
      // if (!inputCourseCodes.includes(courseCode) && courseNames.includes(courseName)) {
      //   addCourseCode(courseCode);
      // }
    });
    if (!(courseCode in courseTypeDictionary) || !(classType in courseTypeDictionary[courseCode]) || !courseTypeDictionary[courseCode][classType]) {
      autoCompleteClassList.appendChild(item);
    }
  });
});
courseInput.addEventListener('input', function() {
  const query = courseInput.value.trim().toUpperCase();
  autoCompleteCourseList.innerHTML = ''; 
  const filteredCourses = courseInfos.filter(code => code.startsWith(query));
  currentCourseIndex = -1; 
  filteredCourses.forEach(course => {
    const item = document.createElement('div');
    item.textContent = course;
    var courseCode = course.split('-')[0].trim();
    item.classList.add('autocomplete-item-course');
    item.addEventListener('click', function () {
      addCourse(course);
      // console.log(courseCodeName, courseCode);
      // if (!inputCourseCodes.includes(courseCode) && courseNames.includes(courseName)) {
      //   addCourseCode(courseCode);
      // }
    });
    if (!inputCourseCodes.includes(courseCode)) {
      autoCompleteCourseList.appendChild(item);
    }
    
  });
});
classInput.addEventListener('keydown', function(e) {
  const items = document.querySelectorAll('.autocomplete-item-class');
  if (items.length == 0) {
    return;
  }
  if (e.key == "ArrowDown") {
    e.preventDefault();
    if (currentClassIndex < items.length - 1) {
      currentClassIndex++;
    }
    else {
      currentClassIndex = 0;
    }
    highlightClassItem(items);
  }
  else if (e.key == "ArrowUp") {
    e.preventDefault();
    if (currentClassIndex > 0) {
      currentClassIndex--;
    }
    else {
      currentClassIndex = items.length - 1;
    }
    highlightClassItem(items);
  }
  else if (e.key == "Enter") {
    e.preventDefault();
    if (currentClassIndex >= 0 && currentClassIndex < items.length) {
      let selectedClass = items[currentClassIndex].textContent;
      var classInfoList = selectedClass.split('-');
      var classCode = classInfoList[0].trim();
      var courseCode = classInfoList[1].trim();
      var classType = classInfoList[2].trim();
      // let selectedCourseCode = selectedCourseName.split('-')[0].trim();
      addClass(selectedClass, classCode, courseCode, classType);
    }
  }
});

courseInput.addEventListener('keydown', function(e) {
  const items = document.querySelectorAll('.autocomplete-item-course');
  if (items.length == 0) {
    return;
  }
  if (e.key == "ArrowDown") {
    e.preventDefault();
    if (currentCourseIndex < items.length - 1) {
      currentCourseIndex++;
    }
    else {
      currentCourseIndex = 0;
    }
    highlightCourseItem(items);
  }
  else if (e.key == "ArrowUp") {
    e.preventDefault();
    if (currentCourseIndex > 0) {
      currentCourseIndex--;
    }
    else {
      currentCourseIndex = items.length - 1;
    }
    highlightCourseItem(items);
  }
  else if (e.key == "Enter") {
    e.preventDefault();
    if (currentCourseIndex >= 0 && currentCourseIndex < items.length) {
      let selectedCourse = items[currentCourseIndex].textContent;
      // let selectedCourseCode = selectedCourseName.split('-')[0].trim();
      addCourse(selectedCourse);
    }
  }
});

function highlightCourseItem(items) {
  console.log(items.length);
  console.log(currentCourseIndex);
  items.forEach((item, index) => {
    if (index === currentCourseIndex) {
      item.classList.add('active'); // Add active class
      item.scrollIntoView({ block: "nearest" }); // Scroll to highlighted item
    } 
    else {
      item.classList.remove('active'); // Remove active class
    }
  });
}

function highlightClassItem(items) {
  console.log(items.length);
  console.log(currentCourseIndex);
  console.log(currentClassIndex);
  items.forEach((item, index) => {
    if (index === currentClassIndex) {
      item.classList.add('active'); // Add active class
      item.scrollIntoView({ block: "nearest" }); // Scroll to highlighted item
    } 
    else {
      item.classList.remove('active'); // Remove active class
    }
  });
}

function addCourse(course) {
  let courseCode = course.split('-')[0].trim()
  console.log("Adding course", course)
  if (!inputCourseCodes.includes(courseCode) && courseInfos.includes(course)) {
    inputCourseCodes.push(courseCode);
    const tagElement = createCourseTagElement(courseCode);
    courseTagsContainer.appendChild(tagElement);
    courseInput.value = ''; // Clear input
    autoCompleteCourseList.innerHTML = ''; // Clear dropdown
    totalCredits += couresCreditDictionary[courseCode];
    creditCounter.textContent = `Tổng số tín chỉ: ${totalCredits}`;
    updateHiddenCourseInput();
    updateClassInfos();
    console.log(hiddenCourseInput.value);
    console.log(inputCourseCodes);
    console.log(classInfos);
    // console.log(timetable)
  }
}
function addClass(classInfo, classCode, courseCode, classType) {
  // let classCode = classInfo.split('-')[0].trim();
  // let courseCode = classInfo.split('-')[1].trim();
  console.log("Adding class", classInfo)
  if (!inputClassCodes.includes(classCode) && classInfos.includes(classInfo)) {
    inputClassCodes.push(classCode);
    const tagElement = createClassTagElement(classCode, courseCode, classType);
    classTagsContainer.appendChild(tagElement);
    classInput.value = ''; // Clear input
    autoCompleteClassList.innerHTML = ''; // Clear dropdown
    if (!(courseCode in courseTypeDictionary)) {
      courseTypeDictionary[courseCode] = {};
    }
    courseTypeDictionary[courseCode][classType] = true;
    updateHiddenClassInput();
    console.log(hiddenClassInput.value);
    console.log(inputClassCodes);
  }
}
function createCourseTagElement(courseCode) {
  if ([...hiddenCourseInput.children].some(tag => tag.textContent.includes(courseCode))) {
    return;
  }
  const tag = document.createElement("div");
  tag.classList.add("course-tag");
  tag.innerHTML = `
    ${courseCode}
    <span class="close-btn">&times;</span>
  `;

  tag.querySelector(".close-btn").addEventListener("click", () => {
    courseTagsContainer.removeChild(tag);
    totalCredits -= couresCreditDictionary[courseCode];
    creditCounter.textContent = `Tổng số tín chỉ: ${totalCredits}`;
    inputCourseCodes = inputCourseCodes.filter((code) => code !== courseCode);
    updateHiddenCourseInput();
  });

  return tag;
}
function createClassTagElement(classCode, courseCode, classType) {

  if ([...hiddenClassInput.children].some(tag => tag.textContent.includes(classCode))) {
    return;
  }
  const tag = document.createElement("div");
  tag.classList.add("class-tag");
  tag.innerHTML = `
    ${classCode + ' - ' + courseCode + ' - ' + classType}
    <span class="close-btn">&times;</span>
  `;

  tag.querySelector(".close-btn").addEventListener("click", () => {
    classTagsContainer.removeChild(tag);
    courseTypeDictionary[courseCode][classType] = false;
    inputClassCodes = inputClassCodes.filter((code) => code !== classCode);
    updateHiddenClassInput();
  });

  return tag;
}
function updateHiddenCourseInput() {
  hiddenCourseInput.value = inputCourseCodes.join(",");
}
function updateHiddenClassInput() {
  hiddenClassInput.value = inputClassCodes.join(",");
}
function updateClassInfos() {
  classInfos = [...new Set(
    timetable
      .filter(row => inputCourseCodes.includes(row[4].trim())) // Filter rows where row[2] is in inputCourseCodes
      .map(row => row[2] + " - " + row[4] + " - " + row[21] + " - " + row[8])
      .map(row => row.trim())
      .filter(Boolean) // Ensure non-empty strings
  )];
}
document.addEventListener('click', function (e) {
  if (!e.target.closest('.autocomplete-container-course')) {
    autoCompleteCourseList.innerHTML = '';
  }
  if (!e.target.closest('.autocomplete-container-class')) {
    autoCompleteClassList.innerHTML = '';
  }
});
populateDropdown("earliest-class-hour-list", earliestHourOptions);
    populateDropdown("latest-class-hour-list", latestHourOptions);