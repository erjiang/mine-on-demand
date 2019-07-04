import { GoogleLogin, GoogleLogout } from 'react-google-login';
import React from 'react';
import './App.css';
import ServerStatus from './ServerStatus';

const ERR_POPUP_CLOSED = 'popup_closed_by_user';

interface AppProps {
}

interface AppState {
  signedIn: boolean,
  isWilted: boolean,
  profileObj?: any,
  googleIDToken?: string,
}

class App extends React.Component<AppProps, AppState> {
  constructor(props: Readonly<AppProps>) {
    super(props);
    this.state = {
      signedIn: false,
      isWilted: false,
    };

    if (!process.env.REACT_APP_GOOGLE_CLIENT_ID) {
      this.onError("Please set the Google client ID in your .env.local file.");
    }
  }

  responseGoogle(response: any) {
    if (response.error) {
      if (response.error === ERR_POPUP_CLOSED) {
        return;
      }
      this.onError("Error logging in to Google: " + response.error);
    } else if (response.profileObj) {
      this.setState({
        signedIn: true,
        profileObj: response.profileObj,
        googleIDToken: response.tokenId,
      });
    }
  }

  onError(msg: string) {
    alert(msg);
    this.setState({ isWilted: true });
  }

  onLogoutSuccess() {
    if (this.state.isWilted) {
      alert("Since you were already wilted, logging in won't do any good.")
    }
    this.setState({
      signedIn: false,
    });
  }

  render() {
    let loginForm = null;
    if (this.state.signedIn) {
      const logoutButton = (
        <div className="logoutButton">
          Signed in as {this.state.profileObj.givenName}.
          {' '}
          <GoogleLogout
            clientId={""}
            buttonText="Logout"
            onLogoutSuccess={() => this.onLogoutSuccess()}
            render={(props) => {
              return <button className="linkLike" onClick={props && props.onClick}>Logout</button>;
            }}
          />.
        </div>
      );
      if (this.state.isWilted) {
        loginForm = logoutButton;
      } else {
        if (this.state.googleIDToken) {
          loginForm = (
            <div>
              <ServerStatus
                googleIDToken={this.state.googleIDToken}
                onError={(msg) => this.onError(msg)}
              />
              {logoutButton}
            </div>
          );
        } else {
          throw new Error("Signed in but Google ID token not set.");
        }
      }
    } else {
      loginForm = (
        <GoogleLogin
          clientId={process.env.REACT_APP_GOOGLE_CLIENT_ID || ""}
          buttonText="Login with Google"
          onSuccess={(response) => this.responseGoogle(response)}
          onFailure={(response) => this.responseGoogle(response)}
          cookiePolicy={"single_host_origin"}
          isSignedIn={true}
        />
      );
    }
    return (
      <div className="App">
        <header className="App-header">
          <span className="minerEmoji" role="img" aria-label="Miner">{this.state.isWilted ? "🥀" : "👷"}</span>
          Mine on Demand
        </header>
        {loginForm}
      </div>
    );
    }
}

export default App;
