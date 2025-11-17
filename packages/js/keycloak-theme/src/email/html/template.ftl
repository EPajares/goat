<#macro emailLayout>
<!DOCTYPE html>
<html lang="${msg("emailLangCode")}" xmlns="http://www.w3.org/1999/xhtml" xmlns:o="urn:schemas-microsoft-com:office:office">
    <head>
        <meta http-equiv="X-UA-Compatible" content="IE=edge" />
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
        <meta name="viewport" content="width=device-width,initial-scale=1" />
        <meta name="x-apple-disable-message-reformatting">
        <title></title>
        <!--[if mso]>
        <noscript>
            <xml>
            <o:OfficeDocumentSettings>
                <o:AllowPNG />
                <o:PixelsPerInch>96</o:PixelsPerInch>
            </o:OfficeDocumentSettings>
            </xml>
        </noscript>
        <![endif]-->
    </head>
  <body
    style="
      font-family: Arial, Open Sans, Helvetica, Arial, sans-serif;
      text-align: center;
      word-spacing: normal;
      background-color: #f8f8f8;
      margin: 0;
      padding: 0;
    "
  >
    <table
      role="presentation"
      style="
        padding: 0;
        border-spacing: 0;
        width: 100%;
        margin-left: auto;
        margin-right: auto;
        max-width: 600px;
        text-align: center;
        align-items: center;
      "
    >
      <thead>
        <tr>
          <td>
            <a href="https://plan4better.de">
              <img
                alt=""
                src="https://assets.plan4better.de/img/logo/plan4better_standard.png"
                style="max-width: 140px; margin-top: 20px; margin-bottom: 20px"
                title=""
              />
            </a>
          </td>
        </tr>
      </thead>
      <tbody style="background: #ffffff; background-color: #ffffff">
        <#nested>
        <tr>
          <td style="padding-top: 40px">
            <p
              style="
                border-top: solid 7px #2bb381;
                margin: 0px auto;
                width: 100%;
              "
            ></p>
          </td>
        </tr>
      </tbody>
      <tfoot
        style="
          text-align: center;
          -webkit-text-size-adjust: 100%;
          -ms-text-size-adjust: 100%;
          color: #c7c8ca;
          font-size: 10px;
          line-height: 15px;
          padding: 5px;
        "
      >
        <tr>
          <td>
            <div style="margin-top: 20px">
              &copy; Plan4Better GmbH 2023 | ${msg("allRightsReserved")}
            </div>
          </td>
        </tr>
        <tr>
          <td>
            <div>
              <a
                href="https://plan4better.de/privacy/"
                style="
                  -webkit-text-size-adjust: 100%;
                  -ms-text-size-adjust: 100%;
                  font-weight: normal;
                  color: #c7c8ca;
                "
                >${msg("privacy")}</a
              >
              |
              <a
                href="https://plan4better.de/kontakt/"
                style="
                  -webkit-text-size-adjust: 100%;
                  -ms-text-size-adjust: 100%;
                  font-weight: normal;
                  color: #c7c8ca;
                "
                >${msg("contactUs")}</a
              >
              |
              <a
                href="https://plan4better.de/team/"
                style="
                  -webkit-text-size-adjust: 100%;
                  -ms-text-size-adjust: 100%;
                  font-weight: normal;
                  color: #c7c8ca;
                "
                >${msg("aboutUs")}</a
              >
            </div>
          </td>
        </tr>
        <tr>
          <td>
            <div
              style="display: inline-flex; margin-top: 5px; text-align: center"
            >
              <a href="https://twitter.com/plan4better"
                ><img
                  alt="Twitter"
                  src="https://assets.plan4better.de/img/icons/twitter_gray.png"
                  style="
                    -ms-interpolation-mode: bicubic;
                    height: auto;
                    outline: none;
                    text-decoration: none;
                    padding-right: 2px;
                    padding-left: 2px;
                    border: 0;
                  "
              /></a>
              <a href="https://www.linkedin.com/company/plan4better/"
                ><img
                  alt="LinkedIn"
                  src="https://assets.plan4better.de/img/icons/linkedin_gray.png"
                  style="
                    -ms-interpolation-mode: bicubic;
                    height: auto;
                    outline: none;
                    text-decoration: none;
                    padding-right: 2px;
                    padding-left: 2px;
                    border: 0;
                  "
              /></a>
            </div>
          </td>
        </tr>
      </tfoot>
    </table>
  </body>
</html>
</#macro>
