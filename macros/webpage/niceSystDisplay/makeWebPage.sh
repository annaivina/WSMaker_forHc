#!/bin/zsh -f



############ HTML webpage creation for nice syst-plot overview
### zsh script !
### Author : Thomas Calvet


###################
############ README
# general "map" syntax : array of strings with group-el1,el2,...
# run me in the folder where I am - I need script.js.template and style.css
# copy output folder in the webpage directory and access with .../outFold/index.html
# you can chmod me and ./ - I actually advice to do so, more stable

echo "-----------------"
echo "Let's get started"

### Control freak ...
shellMode=`ps -p$$ -ocmd= | awk '{print}'`
if [[ ! $shellMode == "zsh" ]] && [[ ! $shellMode == "/bin/zsh -f ./makeWebPage.sh" ]];
then
   echo "You are not in zsh mode --- return 1 --- terminate script"
   return 1
fi

####################
############## SETUP
echo ""
echo "-- setup"

### Generals :
inName="/afs/cern.ch/work/t/tcalvet/workarea/VH/statArea/WSMaker_VHbb/output/SMVHVZ_2019_MVA_mc16ade_v03_STXS.systPlots_fullRes_VHbb_systPlots_0_mc16ade_Systs_mva_STXS_FitScheme_1" ## link to "workdir/output/X"
outFold="sysPlots_L0_06-01-2020" ## web folder link

echo "Get plots from : $inName"
echo "Write in : $outFold"

### Setup syst groups (similar to cov_classification)
classification=(
    "BTag_B-SysFT_EFF_Eigen_B"
    "BTag_C-SysFT_EFF_Eigen_C"
    "BTag_L-SysFT_EFF_Eigen_L"
    "BTagExtrap-SysFT_EFF_extrapolation"
    "Top-TTbar,SysBDTr_ttbar,Sysstop,SysStop"
    "Lepton-SysMUON,SysEL,SysEG"
    "Jet_Eff-SysJET_CR_JET_Eff"
    "Jet_JER-SysJET_CR_JET_JER"
    "Jet_Oth-SysJET_CR_JET_Flavor,SysJET_CR_JET_Pileup,SysJET_CR_JET_Eta,SysJET_CR_JET_BJES"
    "Wjets-WMbb,WPtV,BDTr_W_SHtoMG5,Wbb,Wbc,Wbl,Wcc,Wcl,Wl"
    "Zjets-ZMbb,ZPtV,Zbb,Zbc,Zbl,Zcc,Zcl,Zl"
    "Diboson-WZ,ZZ,WW,VZ,SysVV"
    "VH-VHUEPS,Theory"
    "MJ-MJ"
    "MET-SysMET"
    "LUMI-LUMI"
)

### Sample and region lists
samples=("VHSTXS" "Whf" "Zhf" "ttbar" "diboson" "stop")
allRegions=(
    "L0-BMax250_BMin150_Y6051_DSR_T2_L0_distmva_J2,BMax250_BMin150_Y6051_DSR_T2_L0_distmva_J3,BMin250_Y6051_DSR_T2_L0_distmva_J2,BMin250_Y6051_DSR_T2_L0_distmva_J3"
    "L1-BMax250_BMin150_Y6051_DSR_T2_L1_distmva_J2,BMax250_BMin150_Y6051_DSR_T2_L1_distmva_J3,BMin250_Y6051_DSR_T2_L1_distmva_J2,BMin250_Y6051_DSR_T2_L1_distmva_J3"
    "L2-BMin75_BMax150_Y6051_DSR_T2_L2_distmva_J2,BMin75_BMax150_incJet1_Y6051_DSR_T2_L2_distmva_J3,BMax250_BMin150_Y6051_DSR_T2_L2_distmva_J2,BMax250_BMin150_incJet1_Y6051_DSR_T2_L2_distmva_J3,BMin250_Y6051_DSR_T2_L2_distmva_J2,BMin250_incJet1_Y6051_DSR_T2_L2_distmva_J3"
)
### Get the region in the form of a single list to loop over
### Remove unnecessary ones based on WSMaker nomenclature
regions=""
if [[ $inName =~ "_012_" ]];
then
    region0=`echo ${allRegions[@]:0:1} | cut -d- -f2`
    region1=`echo ${allRegions[@]:1:1} | cut -d- -f2`
    region2=`echo ${allRegions[@]:2:1} | cut -d- -f2`
    regions="${region0},${region1},${region2}"
elif [[ $inName =~ "_0_" ]];
then
    regions=`echo ${allRegions[@]:0:1} | cut -d- -f2`
elif [[ $inName =~ "_1_" ]];
then
    regions=`echo ${allRegions[@]:1:1} | cut -d- -f2`
elif [[ $inName =~ "_2_" ]];
then
    regions=`echo ${allRegions[@]:2:1} | cut -d- -f2`
fi
echo "All lists set : "
echo "Regions : $regions"
echo "Samples : $samples"
echo "Syst classes : $classification"





####################
############ helpers

####################
################ RUN

echo ""
echo "-- start running"
if [ -d $outFold ];
then
   echo "Output folder already exists --- return 1 --- terminate script"
   return 1
fi

echo ""
echo "---- copy all plots"

mkdir ${outFold}
mkdir ${outFold}/pages
for iter in "${classification[@]}"; do
    group=`echo $iter | cut -d- -f1`
    elements=`echo $iter | cut -d- -f2`
    echo " -> $group - $elements"
    el=1
    mkdir ${outFold}/pages/${group}
    while [[ `echo $elements | awk -F, '{print $i}' i=$el` != "" ]]; do
	element=`echo $elements | awk -F, '{print $i}' i=$el`
	let "el=el+1"
	echo "    -> $element at $el"
	cp ${inName}/plots/shapes/*${element}* ${outFold}/pages/${group}
    done
done

echo ""
echo "---- prepare web page"

## central page with links to sub-folds :
echo " -> Generate general index"
echo "Automatically generated html g-index" > ${outFold}/index.html
echo "" >> ${outFold}/index.html
echo "<html>" >> ${outFold}/index.html
echo "<header><title>my VHbb page</title></header>" >> ${outFold}/index.html
echo "<body>" >> ${outFold}/index.html
echo "<section>" >> ${outFold}/index.html
echo "  <h1><u><b>Links to systematic shape control plots :</b></u></h1>" >> ${outFold}/index.html
foreach f (`\ls ${outFold}/pages/`)
    echo "  <h2><a href=\"pages/${f}/myPage.html\">link to $f</a>" >> ${outFold}/index.html
end
echo "</section>" >> ${outFold}/index.html


## plot indexes and display style
echo " -> create web display"
foreach page (`\ls ${outFold}/pages/`)
echo "    -> Now doing : $page"
    ## Copy page style
    cp style.css ${outFold}/pages/${page}

    ## Write page diplay and script
    #### page display header
    echo "<html>" > ${outFold}/pages/${page}/myPage.html
    echo "<!--Automatically generated web page display for WSMaker syst plots-->" >> ${outFold}/pages/${page}/myPage.html
    echo "<!--Many thanks to Rafal Bielski and Johnny Raine from whom the skeleton was provided-->" >> ${outFold}/pages/${page}/myPage.html
    echo "" >> ${outFold}/pages/${page}/myPage.html
    echo "  <head>" >> ${outFold}/pages/${page}/myPage.html
    echo "  <title>SP: $page</title>" >> ${outFold}/pages/${page}/myPage.html
    echo "  <link rel=\"stylesheet\" href=\"style.css\">" >> ${outFold}/pages/${page}/myPage.html
    echo "  <script type=\"text/javascript\" src=\"script.js\"></script>" >> ${outFold}/pages/${page}/myPage.html
    echo "  <meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\">" >> ${outFold}/pages/${page}/myPage.html
    echo "  <!--<meta name=viewport content='width=520'>-->" >> ${outFold}/pages/${page}/myPage.html
    echo "  </head>" >> ${outFold}/pages/${page}/myPage.html
    echo "  " >> ${outFold}/pages/${page}/myPage.html
    echo "  <body onLoad=\"setDefault()\">" >> ${outFold}/pages/${page}/myPage.html
    echo "  <div id =\"header\">" >> ${outFold}/pages/${page}/myPage.html
    echo "    <div id=\"hideoverflow\">" >> ${outFold}/pages/${page}/myPage.html
    echo "    <div id=\"outer\">" >> ${outFold}/pages/${page}/myPage.html
    echo "    <div id=\"inner\">" >> ${outFold}/pages/${page}/myPage.html
    echo "    <div id=\"menu\">" >> ${outFold}/pages/${page}/myPage.html
    echo "      <div class=\"menuBoxLeft\">" >> ${outFold}/pages/${page}/myPage.html
    echo "        <span class=\"menuBoxTitle\">Region</span><br>" >> ${outFold}/pages/${page}/myPage.html
    echo "        <div class=\"menuButtons\">" >> ${outFold}/pages/${page}/myPage.html
    echo "          <button type=\"button\" onclick=\"handleButtonClick(this)\" id=\"selectAllRegs\">All</button>&nbsp;&nbsp;" >> ${outFold}/pages/${page}/myPage.html
    echo "          <button type=\"button\" onclick=\"handleButtonClick(this)\" id=\"selectNoRegs\">None</button>" >> ${outFold}/pages/${page}/myPage.html
    echo "        </div><br>" >> ${outFold}/pages/${page}/myPage.html
    echo "        <div class=\"menuColumn\">" >> ${outFold}/pages/${page}/myPage.html

    #### Handle regions : reformat list for script - add checkbox for page display
    reg=1
    firstReg=""
    regLine="var class_regs = ["
    while [[ `echo $regions | awk -F, '{print $i}' i=$reg` != "" ]]; do
	region=`echo $regions | awk -F, '{print $i}' i=$reg`
	if (( reg == 1 )); then
	    firstReg=$region
	fi
	echo "          <label><input type=\"checkbox\" onclick=\"handleCheckboxClick();\" class=\"cbox $region\">$region</label><br>" >> ${outFold}/pages/${page}/myPage.html
	regLine=$regLine"\"${region}\""
	let "reg=reg+1"
	if [[ `echo $regions | awk -F, '{print $i}' i=$reg` != "" ]]; then
	    regLine=$regLine","
	else
	    regLine=$regLine"]"
	fi
    done

    #### page display intermezzo
    echo "        </div>" >> ${outFold}/pages/${page}/myPage.html
    echo "      </div>" >> ${outFold}/pages/${page}/myPage.html
    echo "" >> ${outFold}/pages/${page}/myPage.html
    echo "      <div class=\"menuBox\">" >> ${outFold}/pages/${page}/myPage.html
    echo "        <span class=\"menuBoxTitle\">Sample</span><br>" >> ${outFold}/pages/${page}/myPage.html
    echo "        <div class=\"menuButtons\">" >> ${outFold}/pages/${page}/myPage.html
    echo "          <button type=\"button\" onclick=\"handleButtonClick(this)\" id=\"selectAllSmps\">All</button>&nbsp;&nbsp;" >> ${outFold}/pages/${page}/myPage.html
    echo "          <button type=\"button\" onclick=\"handleButtonClick(this)\" id=\"selectNoSmps\">None</button>" >> ${outFold}/pages/${page}/myPage.html
    echo "        </div><br>" >> ${outFold}/pages/${page}/myPage.html
    echo "        <div class=\"menuColumn\">" >> ${outFold}/pages/${page}/myPage.html

    #### Handle samples : reformat list for script - add checkbox for page display
    firstSmp=""
    smpLine="var class_smps = ["
    for smp in "${samples[@]}"; do
	smpLine=$smpLine"\"${smp}\""
	echo "          <label><input type=\"checkbox\" onclick=\"handleCheckboxClick();\" class=\"cbox $smp\">$smp</label><br>" >> ${outFold}/pages/${page}/myPage.html
	if [[ $firstSmp == "" ]]; then
	    firstSmp=$smp
	fi
	if [[ $smp == ${samples[-1]} ]]; then
	## if [[ $smp == ${samples[@]:${#samples[@]}-1:1} ]]; then ## if run bash should be this without -1
	    smpLine=$smpLine",\"tot\"]"
	else
	    smpLine=$smpLine","
	fi
    done
    echo "          <label><input type=\"checkbox\" onclick=\"handleCheckboxClick();\" class=\"cbox tot\">tot</label><br>" >> ${outFold}/pages/${page}/myPage.html
    

    #### page display intermezzo
    echo "        </div>" >> ${outFold}/pages/${page}/myPage.html
    echo "      </div>" >> ${outFold}/pages/${page}/myPage.html
    echo "" >> ${outFold}/pages/${page}/myPage.html
    echo "      <div class=\"menuBoxRight\">" >> ${outFold}/pages/${page}/myPage.html
    echo "        <span class=\"menuBoxTitle\">Systematics</span><br>" >> ${outFold}/pages/${page}/myPage.html
    echo "        <div class=\"menuButtons\">" >> ${outFold}/pages/${page}/myPage.html
    echo "          <button type=\"button\" onclick=\"handleButtonClick(this)\" id=\"selectAllSyst\">All</button>&nbsp;&nbsp;" >> ${outFold}/pages/${page}/myPage.html
    echo "          <button type=\"button\" onclick=\"handleButtonClick(this)\" id=\"selectNoSyst\">None</button>" >> ${outFold}/pages/${page}/myPage.html
    echo "        </div><br>" >> ${outFold}/pages/${page}/myPage.html
    echo "" >> ${outFold}/pages/${page}/myPage.html
    echo "        <div class=\"menuColumn\">" >> ${outFold}/pages/${page}/myPage.html


    #### Handle systs : get list for script - add checkbox for page display
    systList=()
    foreach plot (`\ls ${outFold}/pages/${page}/ | grep ".png" | grep -v ratio | grep -v distpTV | grep -v distMET`)
        nameEl=1
	systName=""
	goInName=0
	while [[ `echo $plot | cut -d. -f1 | awk -F_ '{print $i}' i=$nameEl` != "" ]]; do
	    substring=`echo $plot | cut -d. -f1 | awk -F_ '{print $i}' i=$nameEl`
	    if [[ $substring == "Sys"* ]]; then
		goInName=1
		systName=$substring
	    elif (( $goInName == 1 )); then
		 systName="${systName}_${substring}"
	    fi
	    let "nameEl+=1"
	done
	if [[ ${systList[(ie)$systName]} -ge ${#systList}+1 ]]; then
	    systList+=( $systName )
	    echo "          <label><input type=\"checkbox\" onclick=\"handleCheckboxClick();\" class=\"cbox $systName\">$systName</label><br>" >> ${outFold}/pages/${page}/myPage.html
	fi
    end
    echo "      -> Sys List : "$systList
    

    #### page display intermezzo
    echo "        </div>" >> ${outFold}/pages/${page}/myPage.html
    echo "      </div>" >> ${outFold}/pages/${page}/myPage.html
    echo "    </div>" >> ${outFold}/pages/${page}/myPage.html
    echo "    </div>" >> ${outFold}/pages/${page}/myPage.html
    echo "    </div>" >> ${outFold}/pages/${page}/myPage.html
    echo "    </div>" >> ${outFold}/pages/${page}/myPage.html
    echo "    " >> ${outFold}/pages/${page}/myPage.html
    echo "    <div class=\"hidewrapper\">" >> ${outFold}/pages/${page}/myPage.html
    echo "      <button type=\"button\" onclick=\"hideMenuBar();\" id=\"hideMenuButton\">Show/Hide</button>" >> ${outFold}/pages/${page}/myPage.html
    echo "    </div>" >> ${outFold}/pages/${page}/myPage.html
    echo "  </div>" >> ${outFold}/pages/${page}/myPage.html
    echo "" >> ${outFold}/pages/${page}/myPage.html
    echo "" >> ${outFold}/pages/${page}/myPage.html
    echo "  <div id=\"pagewrap\">" >> ${outFold}/pages/${page}/myPage.html
    echo "  <!-- START PLOTS -->" >> ${outFold}/pages/${page}/myPage.html

    #### add all plots to page display
    echo "" >> ${outFold}/pages/${page}/myPage.html
    echo "" >> ${outFold}/pages/${page}/myPage.html
    echo "" >> ${outFold}/pages/${page}/myPage.html
    foreach plot (`\ls ${outFold}/pages/${page}/ | grep ".png" | grep -v distpTV | grep -v distMET`)
        reg=""
	ireg=1
	while [[ `echo $regions | awk -F, '{print $i}' i=$ireg` != "" ]]; do
	    region=`echo $regions | awk -F, '{print $i}' i=$ireg`
	    if [[ $plot == *${region}* ]]; then
		reg=$region
		break
	    else
		let "ireg+=1"
	    fi
	done
        smp=""
	for ismp in "${samples[@]}"; do
	    if [[ $plot == *${ismp}_Sys* ]]; then
		smp=$ismp
	    fi
	done
	if [[ $smp == "" ]]; then
	    smp="tot"
	fi
        nameEl=1
	sys=""
	goInName=0
	while [[ `echo $plot | cut -d. -f1 | awk -F_ '{print $i}' i=$nameEl` != "" ]]; do
	    substring=`echo $plot | cut -d. -f1 | awk -F_ '{print $i}' i=$nameEl`
	    if [[ $substring == "Sys"* ]]; then
		goInName=1
		sys=$substring
	    elif [[ $substring == "ratio" ]]; then
		let "nameEl+=1"
		continue
	    elif (( $goInName == 1 )); then
		 sys="${sys}_${substring}"
	    fi
	    let "nameEl+=1"
	done
	echo "<a href=\"${plot}\" download=\"${plot}\"><img src=\"${plot}\" id=\"${plot}\" class=\"plot $reg $smp $sys\" alt=\"${plot}\"></a>" >> ${outFold}/pages/${page}/myPage.html
    end
    echo "" >> ${outFold}/pages/${page}/myPage.html
    echo "" >> ${outFold}/pages/${page}/myPage.html
    echo "" >> ${outFold}/pages/${page}/myPage.html

    #### page display intermezzo - close
    echo "  <!-- END PLOTS -->" >> ${outFold}/pages/${page}/myPage.html
    echo "  </div>  " >> ${outFold}/pages/${page}/myPage.html
    echo "  </body>" >> ${outFold}/pages/${page}/myPage.html
    echo "" >> ${outFold}/pages/${page}/myPage.html
    echo "" >> ${outFold}/pages/${page}/myPage.html
    echo "</html>" >> ${outFold}/pages/${page}/myPage.html

    #### Handle systs : reformat list for script
    firstSyst=""
    systLine="var class_systs = ["
    for syst in "${systList[@]}"; do
	systLine=$systLine"\"${syst}\""
	if [[ $firstSyst == "" ]]; then
	    firstSyst=$syst
	fi
	if [[ $syst == ${systList[-1]} ]]; then
	## if [[ $syst == ${samples[@]:${#samples[@]}-1:1} ]]; then ## if run bash should be this without -1
	    systLine=$systLine"]"
	else
	    systLine=$systLine","
	fi
    done

    #### Write script.js
    echo $regLine > ${outFold}/pages/${page}/script.js
    echo $smpLine >> ${outFold}/pages/${page}/script.js
    echo $systLine >> ${outFold}/pages/${page}/script.js

    echo "" >> ${outFold}/pages/${page}/script.js
    echo "var menu_show = true;" >> ${outFold}/pages/${page}/script.js
    echo "var is_mobile = false;" >> ${outFold}/pages/${page}/script.js

    echo "" >> ${outFold}/pages/${page}/script.js
    echo "function setDefault(){" >> ${outFold}/pages/${page}/script.js
    echo "    document.getElementsByClassName(\"cbox $firstReg\")[0].checked = true;" >> ${outFold}/pages/${page}/script.js
    echo "    document.getElementsByClassName(\"cbox $firstSmp\")[0].checked = true;" >> ${outFold}/pages/${page}/script.js
    echo "    document.getElementsByClassName(\"cbox $firstSyst\")[0].checked = true;" >> ${outFold}/pages/${page}/script.js
    echo "    handleCheckboxClick();" >> ${outFold}/pages/${page}/script.js
    echo "}" >> ${outFold}/pages/${page}/script.js

    echo "" >> ${outFold}/pages/${page}/script.js
    cat script.js.template >> ${outFold}/pages/${page}/script.js

end


echo "I'm done :)"
