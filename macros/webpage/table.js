function filterFiles (fText) {
  if (fText.length < 3) {
    return files;
  }
  var regex = new RegExp(fText, 'i');
  return files.filter(function(f) { return regex.test(f[0]); })
};

// test real equality of two arrays.
function arrayEquality (a1, a2) {
return (a1.length===a2.length && a1.every(function(v,i) { return v[0] === a2[i][0]}));
};

function createCell (f) {
  fname = f[0];
  var cell = document.createElement("article");
  var link = document.createElement("a");
  if(f[3]) {
    link.href="showROOT.html?file="+fname.replace(".png", ".root")+"&item=c;1&noselect&mathjax";
  }
  else {
    link.href=fname;
  }
  var img = document.createElement("img");
  img.src = fname;
  link.appendChild(img);
  cell.appendChild(link);
  var par = document.createElement("p");
  var linkpng = document.createElement("a");
  linkpng.href=fname;
  linkpng.appendChild(document.createTextNode(fname));
  par.appendChild(linkpng);
  if(f[1]) {
    par.appendChild(document.createTextNode(" / "));
    var linkeps = document.createElement("a");
    linkeps.href=fname.replace(".png", ".eps");
    linkeps.appendChild(document.createTextNode(".eps"));
    par.appendChild(linkeps);
  }
  if(f[2]) {
    par.appendChild(document.createTextNode(" / "));
    var linkpdf = document.createElement("a");
    linkpdf.href=fname.replace(".png", ".pdf");
    linkpdf.appendChild(document.createTextNode(".pdf"));
    par.appendChild(linkpdf);
  }
  cell.appendChild(par);
  return cell;
};

function createTable (flist) {
  console.log("Creating a table of "+flist.length+" elements");

  var images = [];
  // Create and Populate the rows of the table
  flist.forEach(function(f) {
    images.push(createCell(f))
  });
  /*console.log(images);*/

  var imagesElt = document.getElementById("images");
  existingImages = imagesElt.getElementsByTagName("article");
  /*console.log(existingRows);*/
  // Empty the table if it has been filled previously
  if(existingImages.length > 0) {
    imagesElt.innerHTML = "";
  }
  // Add the new rows
  images.forEach(function(i) {
    imagesElt.appendChild(i);
  });

};

// First, fill everything

createTable(files);

// Then, filter if needed

var lastFilteredList = files;
var filterElt = document.getElementById("filter");
filterElt.addEventListener("input", function (e) {
  var newFilteredList = filterFiles(e.target.value);
  if(! arrayEquality(newFilteredList, lastFilteredList)) {
    createTable(newFilteredList);
    lastFilteredList = newFilteredList;
    console.log("Contents have been refreshed");
  }
});

