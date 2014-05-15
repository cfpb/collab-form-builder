var textAreas = document.getElementsByTagName("TEXTAREA");
var thisArea;
var countRemaining;
var counterPretty;
var counterSign;
var textAreaLength;
var countNewLines;
for (var i = 0; i < textAreas.length; i++) {
	thisArea = document.getElementById(textAreas[i].getAttribute("id"));
	setCounter(thisArea);
}

if (history.length === 1) { //if we got here directly from a link
	$(document.getElementById("button-id-cancel")).click(function(){window.location.assign("/");});
} else {
	$(document.getElementById("button-id-cancel")).click(function(){window.history.back();});
}

function setCounter(obj) {
	$(obj).keyup(function(){countText(this);});
	$(obj).blur(function(){countText(this);}); //handle mouse-only actions
	//note that jQuery's .change() action only takes effect on blur anyway
}

function countText(elem) {
    textAreaLength = elem.value.length;

    /*
    ::NEWLINE ISSUE::
    Javascript, Python and the HTML DOM treat multiline strings differently. Moreover, since
    the HTML DOM is interpreted by the browser different versions of Chrome, IE, Firefox, etc.
    have treated a line break differently over time. The majority, it appears, favors treating
    a line break as two characters (/n/r). This is how Python counts multiline strings as
    well. Javascript appears to be consistent in counting a line break as one character (/n).

    This is all complicated further by the fact that a user expects a line break to count as
    zero characters. The behavior coded here adjusts the calculation of the string length,
    the upshot of which results in line breaks being ignored.

    Furthermore, as the HTML DOM interpretation is unpredictable there is no enforcement of
    field length where it would normally be (i.e.: in a "maxlength" parameter of the TEXTAREA
    field); if we added this parameter we would get unpredictable results for field inputs
    near 2,500 characters in length with line breaks. Since we can't override the browser's
    interpretation of the DOM, the only client-side validation is in Javascript.

    There is code in forms.py that enforces the field length on the back end.
    */
    countNewLines = (elem.value.match(/\n/g) || []).length;
	countRemaining = (2500 - textAreaLength + countNewLines);

    //prevent users from entering too much text
	if (countRemaining < 0) {
		elem.value = elem.value.toString().slice(0, (2500 + countNewLines));
		countRemaining = 0;
	}

    //add commas for thousands separator
	counterPretty = countRemaining.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
	counterSign = (elem.id + "_textcount").toString().slice(3);
	document.getElementById(counterSign).innerHTML = "You have " + counterPretty + " characters remaining.";
}