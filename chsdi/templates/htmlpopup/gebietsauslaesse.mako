<%inherit file="base.mako"/>

<%def name="table_body(c, lang)">
<%
    kanal = 'kanal_%s' % lang
%>

    <tr><td class="cell-left">${_('tt_ezgnr')}</td>    <td>${c['attributes']['ezgnr'] or '-'}</td></tr>
    <tr><td class="cell-left">${_('klwkp_gwlnr')}</td>          <td>${c['attributes']['gwlnr'] or '-'}</td></tr>
    <tr><td class="cell-left">${_('tt_measure_2')}</td>         <td>${c['attributes']['measure'] or '-'}</td></tr>
    <tr><td class="cell-left">${_('tt_ezgflaeche')}</td>         <td>${c['attributes']['gesamtflae'] or '-'}</td></tr>
    <tr><td class="cell-left">${_('tt_anteil_ch')}</td>         <td>${c['attributes']['anteil_ch'] or '-'}</td></tr>
    <tr><td class="cell-left">${_('gewaesser')}</td>         <td>${c['attributes']['gewaessern'] or '-'}</td></tr>
    <tr><td class="cell-left">${_('tt_kanal')}</td>       <td>${c['attributes'][kanal] or '-'}</td></tr>
</%def>

