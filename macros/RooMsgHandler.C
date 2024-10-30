#include <RooGlobalFunc.h>
#include <RooMsgService.h>
#include <fstream>
#include <sstream>
#include <string>

using namespace std;

namespace LimitCrossCheck {

  /**
   * Captures RooFit evaluation and plotting errors and dumps them into a file when going out of scope.
   */
  class RooMsgHandler {
   public:
    /**
     * Constructor
     * @param outdirName Directory to write to.
     * @param callerName A string to identify the caller e.g. '__func__ + <arbitray string>'
     * @param reportStream An ostream to report to when roofit signals errors/warnings.
     * @param topics Message topics to be intercepted.
     */
    RooMsgHandler(const char* outdirName, const char* callerName, ostream& reportStream,
                  int topics = RooFit::Eval | RooFit::Plotting) :
        m_errorStream(),
        m_outdirName(outdirName),
        m_callerName(callerName),
        m_reportStream(reportStream),
        m_streamID(-1),
        m_topics(RooFit::MsgTopic(topics)),
        m_lastTellp(m_errorStream.tellp())
    {
      RooMsgService& msv = RooMsgService::instance();
      m_streamID         = msv.addStream(RooFit::WARNING, RooFit::Topic(m_topics), RooFit::OutputStream(m_errorStream));
      msv.getStream(0).removeTopic(m_topics);
      msv.getStream(1).removeTopic(m_topics);
    }

    ~RooMsgHandler()
    {
      write();

      RooMsgService& msv = RooMsgService::instance();
      msv.getStream(0).addTopic(m_topics);
      msv.getStream(1).addTopic(m_topics);
      msv.deleteStream(m_streamID);
    }

    void limitMemoryFootprint(ostream::pos_type limit = 1024 * 1024 * 2)
    { // 2Mb
      if( m_errorStream.tellp() > limit ) {
        m_errorStream.seekp(0, ios_base::beg);
        m_reportStream << "Discarding " << limit / 1024 << " kb of buffered evaluation/plotting error messages from "
                       << m_callerName << ". The rest will go to " << makeFilename() << " at exit." << endl;
      }
    }

    void newCallerName(string callerName)
    {
      write();
      m_errorStream.str("");
      m_callerName = callerName;
    }

    bool hasNewErrors(ostream::pos_type threshold = 0)
    {
      ostream::pos_type oldtellp = m_lastTellp;
      return (m_lastTellp = m_errorStream.tellp()) - oldtellp > threshold;
    }

   private:
    string makeFilename() const { return m_outdirName + "/evaluationErrors_" + m_callerName + ".txt"; }

    void write()
    {
      string filename = makeFilename();
      m_errorStream.seekp(0, ios_base::end);
      if( m_errorStream.tellp() ) {
        m_reportStream << "\n\nRecorded RooFit errors/warnings during " << m_callerName << ".\n"
                       << "See " << filename << " for details." << endl;

        ofstream outfile(filename.c_str(), ios::trunc);
        outfile << m_errorStream.str();
      }
    }

    ostringstream     m_errorStream;
    string            m_outdirName;
    string            m_callerName;
    ostream&          m_reportStream;
    int               m_streamID;
    RooFit::MsgTopic  m_topics;
    ostream::pos_type m_lastTellp;
  };

} // namespace LimitCrossCheck
