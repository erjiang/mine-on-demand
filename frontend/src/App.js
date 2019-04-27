import GoogleLogin from 'react-google-login';
import React from 'react';
import './App.css';
import ServerStatus from './ServerStatus';

class App extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      signedIn: false,
      wilted: false,
    };
  }

  responseGoogle(response) {
    if (response.error) {
      console.log("Error");
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
    this.setState({ wilted: true });
  }

  render() {
    let loginForm = null;
    if (this.state.signedIn) {
      if (this.state.wilted) {
        loginForm = null;
      } else {
        loginForm = (
          <div>
            <p>You are signed in, {this.state.profileObj.givenName}.</p>
            <ServerStatus
              googleIDToken={this.state.googleIDToken}
              onError={(msg) => this.onError(msg)}
            />
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
          <span className="minerEmoji" role="img" aria-label="Miner">{this.state.wilted ? "🥀" : "👷‍♀️"}</span>
          Mine on Demand
        </header>
        {loginForm}
      </div>
    );
    }
}

export default App;
