import * as XLSX from 'xlsx';
//f = file
var name = f.name;
const reader = new FileReader();
reader.onload = (evt) => { // evt = on_file_select event
    /* Parse data */
    const bstr = evt.target.result;
    const wb = XLSX.read(bstr, {type:'binary'});
    /* Get first worksheet */
    const wsname = wb.SheetNames[0];
    const ws = wb.Sheets[wsname];
    /* Convert array of arrays */
    const data = XLSX.utils.sheet_to_csv(ws, {header:1});
    /* Update state */
    console.log("Data>>>"+data);
};
reader.readAsBinaryString(f);