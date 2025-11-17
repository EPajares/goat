<#import "template.ftl" as layout>
<@layout.emailLayout>
    <tr>
      <td style="padding-top: 40px;">
        <img
            alt=""
            src="https://assets.plan4better.de/img/email/verify_email.png"
            style="width: 250px"
        />
      </td>
    </tr>
    <tr>
      <td>
        <div style="${properties.titleStyle}">
          <h2>${msg("eventLoginErrorTitle")}</h2>
        </div>
      </td>
    </tr>
    <tr>
      <td>
        <div
          style="${properties.infoContentStyle}"
        >
          ${kcSanitize(msg("eventLoginErrorBodyHtml",event.date,event.ipAddress))?no_esc}
        </div>
      </td>
    </tr>
</@layout.emailLayout>