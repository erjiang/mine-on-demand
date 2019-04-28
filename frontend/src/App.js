import { GoogleLogin, GoogleLogout } from 'react-google-login';
import React from 'react';
import './App.css';
import ServerStatus from './ServerStatus';

class App extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      signedIn: false,
      isWilted: false,
    };
  }

  responseGoogle(response) {
    if (response.error) {
      this.onError("Error logging in to Google.");
    } else if (response.profileObj) {
      this.setState({
        signedIn: true,
        profileObj: response.profileObj,
        googleIDToken: response.tokenId,
      });
    }
  }

  onError(msg) {
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
            buttonText="Logout"
            onLogoutSuccess={() => this.onLogoutSuccess()}
            icon={false}
            render={(props) => {
              return <a href="#" onClick={props.onClick}>Logout</a>;
            }}
          />.
        </div>
      );
      if (this.state.isWilted) {
        loginForm = logoutButton;
      } else {
        loginForm = (
          <div>
            <ServerStatus
              googleIDToken={this.state.googleIDToken}
              onError={(msg) => this.onError(msg)}
            />
            {logoutButton}
          </div>
        );
      }
    } else {
      loginForm = (
        <GoogleLogin
          clientId="834173658994-kirouiivjlfkfecl2nemtu1q79d9p5u4.apps.googleusercontent.com"
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
