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
          <h2>${msg("emailTestTitle")}</h2>
        </div>
      </td>
    </tr>
    <tr>
      <td>
        <div
          style="${properties.infoContentStyle}"
        >
          ${kcSanitize(msg("emailTestBodyHtml"))?no_esc}
        </div>
      </td>
    </tr>
    <tr>
      <td>
        <a
          href="https://auth.plan4better.de"
          style="${properties.actionButtonStyle}"
        >
          <b style="font-weight: 700">${msg("emailTestButton")}</b>
        </a>
      </td>
    </tr>
</@layout.emailLayout>