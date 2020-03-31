# Replacing text within Slack's desktop client automatically
In response to workplace sexual harassment, it became too traumatic to continue working while seeing slack messages from the person who had caused pain but managed to remain at the company. As a technological measure in the company Slack, this project was created to rewrite the name of the abusive person in real time.

It is worth noting that I did obtain a restraining order against this sexual harasser and that my claims against him are legally documented in relevant court hearings and are not to be considered libel nor grounds for takedown of this content.

## How does it work
Slack is built on web technologies like [Electron](https://github.com/electron/electron) and can be modified locally. This project injects javascript code that is loaded on Slack's startup. The injected code does simple string replacement on messages and sender names. This approach is not officially supported and is likely to break after an update.

## Installation
Customize the map of replacements, which is a dictionary from search terms to replacement terms.
Run
```shell
python3 slack-replace-install.py
```
and then restart your desktop slack client. 

## Versions of Slack
This has only been tested against Slack 4.4.1. If the major version is different it may no longer work. Previous versions of Slack are tagged to be functional in the repo, including: 4.3.3.

## Updating Slack
After slack has updated, re-run the install script.

## Debugging
If something breaks due to an update in slack and you would like to try to fix it, it helps to view the developer menu. Run
```shell
export SLACK_DEVELOPER_MENU=true; open -a /Applications/Slack.app
```
which allows a "View->Developer Tools" menu that has inspectors and a console.

## Future development
* Since this was a corporate environment it remained useful to still see the offender's messages. Support for completely blocking messages should be able to be implemented. Other approaches at putting user blocking into slack do similar tricks to identify messages and then hidem them like
```js
    messageElement.classList.add("blocked");
    messageElement.style.display = "none";
```

* To detect messages by particular users, one needs to delay the parsing as at the time of DOM insertion the sender has not been updated. However, after a short delay, using `'data-member-id'` or a class of `c-message__sender_link` may be possible to detect the user ID.

* Needs to be changed to a setup.py structure as a tool.

* Needs linting and testing to support it as future development.

## Alternatives
One can get the same effect using the browser client and an extension like [FoxReplace](https://addons.mozilla.org/en-US/firefox/addon/foxreplace/)

## Acknowledgements
https://github.com/ketanbhatt/block-slack-users
https://github.com/fsavje/math-with-slack
https://github.com/thisiscam/math-with-slack

## Consent
Respect the consent of your co-workers. If they say no and don't want to interact, leave them alone. Sexual harassment is immoral via any method of communication.
