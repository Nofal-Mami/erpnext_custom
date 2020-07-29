<div align="center">
    <img src="https://raw.githubusercontent.com/frappe/erpnext/develop/erpnext/public/images/erpnext-logo.png" height="128">
    <h2>Tunisia Account ERPNext Customization</h2>
    <p align="center">
        <p>Tunisia Account ERPNext Customization</p>
    </p>

[![Build Status](https://travis-ci.com/frappe/erpnext.svg)](https://travis-ci.com/frappe/erpnext)
</div>

How to setup app on frappe bench 

1. Backup current site with command below<br>
    `bench backup --with-files` to backup with files

1. Pull app code from git repository using command below<br>
`bench get-app https://github.com/maisonarmani/erpnext_custom erpnext_custom`

1. Install app<br>
`bench --site sitename install-app erpnext_custom`

1. Run a bench migrate with the command below<br>
`bench migrate --site site-name` or `bench migrate` for all sites 

1. Setup the tunisia account configuration in the Tunisia Accounting module.


<h4>Tunisia account configuration</h4>

H1: Group headings<br>
    &nbsp;&nbsp;&nbsp;H2: Sub headings/Group Total<br>
  &nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;H3/HO: Net / Group seperation <br>
 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
 H4: Group Item
 
Have fun !!!
